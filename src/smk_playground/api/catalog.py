"""Read-only in-memory catalog over frozen compact Parquet artifacts."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from smk_playground.enrichment.milestone6 import WeightedSimilarityEngine
from smk_playground.normalize.milestone4 import sha256_file
from smk_playground.similarity.engine import SimilarityEngine
from smk_playground.sonification.profiles import (
    palette_arpeggio,
    physical_artwork_tone,
    weighted_color_tone,
)


class Catalog:
    def __init__(self, root: Path):
        self.root = root
        required = [
            root / "data" / "processed" / "web-catalog-v1.parquet",
            root / "data" / "processed" / "artwork-weighted-palettes-v1.parquet",
            root / "data" / "processed" / "similarity-profiles-v1.json",
            root / "data" / "processed" / "similarity-profiles-v2.json",
            root / "data" / "processed" / "sonification-profiles-v1.json",
        ]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise RuntimeError("Missing required processed artifacts: " + ", ".join(missing))
        self.rows = pq.read_table(required[0]).to_pylist()
        self.by_id = {row["smk_entity_id"]: row for row in self.rows}
        self.by_number: dict[str, list[dict[str, Any]]] = {}
        for row in self.rows:
            self.by_number.setdefault(row["object_number"], []).append(row)
        palette_rows = pq.read_table(required[1]).to_pylist()
        self.palettes: dict[str, list[dict[str, Any]]] = {}
        for row in palette_rows:
            self.palettes.setdefault(row["smk_entity_id"], []).append(row)
        for values in self.palettes.values():
            values.sort(key=lambda row: row["palette_rank"])
        self.fast_similarity = SimilarityEngine(root)
        self._weighted_similarity: WeightedSimilarityEngine | None = None
        self.weighted_profile_hash = sha256_file(required[3])
        self.cache_dir = root / "data" / "cache" / "weighted-similarity"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def weighted_similarity(self) -> WeightedSimilarityEngine:
        if self._weighted_similarity is None:
            self._weighted_similarity = WeightedSimilarityEngine(self.root)
        return self._weighted_similarity

    def public_card(self, row: dict[str, Any]) -> dict[str, Any]:
        return {key: row.get(key) for key in (
            "smk_entity_id", "object_number", "display_title", "artist_display", "date_text",
            "classification", "image_thumbnail", "centroid_chroma", "dominant_color_hex",
        )}

    def search(self, query: str, limit: int, offset: int, classification: str | None,
               has_physical: bool | None, chromatic: bool | None) -> dict[str, Any]:
        needle = query.casefold().strip()
        matches = []
        for row in self.rows:
            if needle and needle not in row["search_text"]:
                continue
            if classification and classification.casefold() not in (row.get("classification") or "").casefold():
                continue
            if has_physical is not None:
                present = row.get("net_width_cm") is not None and row.get("net_height_cm") is not None
                if present != has_physical:
                    continue
            if chromatic is not None:
                present = row.get("centroid_hue_deg") is not None
                if present != chromatic:
                    continue
            matches.append(row)
        return {"total": len(matches), "limit": limit, "offset": offset,
                "items": [self.public_card(row) for row in matches[offset:offset + limit]]}

    def artwork(self, entity_id: str) -> dict[str, Any]:
        if entity_id not in self.by_id:
            raise KeyError(entity_id)
        row = self.by_id[entity_id]
        palette = self.palettes.get(entity_id, [])
        feature = row
        normalized = row
        return {
            **{key: row.get(key) for key in (
                "smk_entity_id", "object_number", "title_da", "title_en", "display_title",
                "artist_display", "date_text", "classification", "image_iiif_id",
                "image_thumbnail", "image_native", "image_width", "image_height",
                "rights_semantic", "net_width_cm", "net_height_cm", "quality_flags",
            )},
            "weighted_palette": [{key: item.get(key) for key in (
                "palette_rank", "hex", "token_count", "weight", "oklab_l", "oklab_a",
                "oklab_b", "oklch_c", "oklch_h_deg")}
                for item in palette],
            "weighted_features": {key: row.get(key) for key in (
                "centroid_l", "centroid_a", "centroid_b", "centroid_chroma",
                "centroid_hue_deg", "palette_entropy", "palette_entropy_01",
                "effective_palette_size", "palette_spread_oklab", "chroma_stddev",
                "hue_concentration_01", "dominant_color_hex", "dominant_color_weight",
                "weighted_palette_status")},
            "sonification": {
                "weighted_color": weighted_color_tone(feature),
                "physical": physical_artwork_tone(feature, normalized),
                "palette_arpeggio": palette_arpeggio(palette),
            },
            "provenance": {
                "metadata": "SMK bulk open data",
                "palette_weights": "SMK enrichment colorextractor token frequencies",
                "features": "SMK Playground derived weighted features v2",
                "sonification": "SMK Playground deterministic artistic mappings v1",
            },
        }

    def resolve(self, object_number: str) -> list[dict[str, Any]]:
        return [self.public_card(row) for row in self.by_number.get(object_number, [])]

    def random(self, seed: int | None) -> dict[str, Any]:
        rng = random.Random(seed) if seed is not None else random.SystemRandom()
        return self.public_card(self.rows[rng.randrange(len(self.rows))])

    def similar(self, entity_id: str, profile: str, limit: int) -> dict[str, Any]:
        if entity_id not in self.by_id:
            raise KeyError(entity_id)
        if profile == "weighted-color":
            return self._weighted_cached(entity_id, limit)
        query = self.fast_similarity.resolve(smk_entity_id=entity_id)
        results = self.fast_similarity.search_row(query, profile, limit)
        return {"profile": profile, "cached": False,
                "items": [self._similar_item(item) for item in results]}

    def _similar_item(self, result: dict[str, Any]) -> dict[str, Any]:
        catalog = self.by_id[result["smk_entity_id"]]
        return {**self.public_card(catalog), "rank": result["rank"],
                "distance": result["total_distance"],
                "active_components": result["active_components"],
                "components": result["components"]}

    def _weighted_cached(self, entity_id: str, limit: int) -> dict[str, Any]:
        cache_limit = max(50, limit)
        cache_path = self.cache_dir / f"{entity_id}.json"
        if cache_path.exists():
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            if (payload.get("profile_hash") == self.weighted_profile_hash
                    and payload.get("max_results", 0) >= limit):
                return {"profile": "weighted-color", "cached": True,
                        "items": payload["items"][:limit]}
        query = self.weighted_similarity.resolve(smk_entity_id=entity_id)
        results = self.weighted_similarity.search_row(query, cache_limit)
        items = [self._similar_item(item) for item in results]
        payload = {"profile": "weighted-color", "profile_hash": self.weighted_profile_hash,
                   "max_results": cache_limit, "items": items}
        temporary = cache_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        temporary.replace(cache_path)
        return {"profile": "weighted-color", "cached": False, "items": items[:limit]}

    def stats(self) -> dict[str, Any]:
        return {
            "artwork_count": len(self.rows),
            "weighted_palette_count": sum(bool(row["has_weighted_palette_v1"]) for row in self.rows),
            "physical_geometry_count": sum(
                row.get("net_width_cm") is not None and row.get("net_height_cm") is not None
                for row in self.rows
            ),
        }

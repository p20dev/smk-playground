"""Build deterministic compact catalog and sonification profile manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from smk_playground.normalize.milestone4 import sha256_file
from smk_playground.sonification.profiles import profile_manifest


def _json(value: str | None) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _first_text(value: str | None, *keys: str) -> str | None:
    parsed = _json(value)
    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, str) and item.strip():
                return item.strip()
            if isinstance(item, dict):
                for key in keys:
                    candidate = item.get(key)
                    if candidate:
                        return str(candidate).strip()
    return None


def run(root: Path) -> dict[str, Any]:
    artworks_path = root / "data" / "processed" / "artworks.parquet"
    features_path = root / "data" / "processed" / "artwork-visual-features-v2.parquet"
    normalized_path = root / "data" / "processed" / "artwork-normalized-features-v1.parquet"
    artwork_columns = [
        "smk_entity_id", "object_number", "titles_da_json", "titles_en_json",
        "artists_da_json", "artists_en_json", "production_dates_da_json",
        "object_names_da_json", "object_names_en_json", "classifications_da_json",
        "classifications_en_json", "image_iiif_id", "image_thumbnail", "image_native",
        "image_width", "image_height", "rights_semantic", "net_width_cm", "net_height_cm",
        "quality_flags", "corpus_smk_public_visual_v1",
    ]
    canonical = {
        row["smk_entity_id"]: row for row in pq.read_table(
            artworks_path, columns=artwork_columns,
            filters=[("corpus_smk_public_visual_v1", "=", True)],
        ).to_pylist()
    }
    feature_columns = [
        "smk_entity_id", "centroid_l", "centroid_a", "centroid_b", "centroid_chroma",
        "centroid_hue_deg", "palette_entropy", "palette_entropy_01", "effective_palette_size",
        "palette_spread_oklab", "chroma_stddev", "hue_concentration_01",
        "dominant_color_hex", "dominant_color_weight", "has_weighted_palette_v1",
        "weighted_palette_status",
    ]
    features = {row["smk_entity_id"]: row for row in pq.read_table(
        features_path, columns=feature_columns
    ).to_pylist()}
    normalized = {row["smk_entity_id"]: row for row in pq.read_table(
        normalized_path, columns=["smk_entity_id", "log_net_area_cm2_percentile_01",
                                  "log_net_aspect_ratio"]
    ).to_pylist()}
    rows = []
    for entity_id in sorted(canonical):
        source, feature, norm = canonical[entity_id], features[entity_id], normalized[entity_id]
        title_da = _first_text(source["titles_da_json"], "title")
        title_en = _first_text(source["titles_en_json"], "title")
        artist = _first_text(source["artists_da_json"]) or _first_text(source["artists_en_json"])
        date_text = _first_text(source["production_dates_da_json"], "period", "start")
        classification = (
            _first_text(source["classifications_da_json"], "name", "classification")
            or _first_text(source["object_names_da_json"], "name")
            or _first_text(source["classifications_en_json"], "name", "classification")
            or _first_text(source["object_names_en_json"], "name")
        )
        rows.append({
            "smk_entity_id": entity_id, "object_number": source["object_number"],
            "title_da": title_da, "title_en": title_en, "display_title": title_da or title_en or source["object_number"],
            "artist_display": artist, "date_text": date_text, "classification": classification,
            "search_text": " ".join(filter(None, (source["object_number"], title_da, title_en, artist, classification))).casefold(),
            "image_iiif_id": source["image_iiif_id"], "image_thumbnail": source["image_thumbnail"],
            "image_native": source["image_native"], "image_width": source["image_width"],
            "image_height": source["image_height"], "rights_semantic": source["rights_semantic"],
            "net_width_cm": source["net_width_cm"], "net_height_cm": source["net_height_cm"],
            "quality_flags": source["quality_flags"], **feature,
            "log_net_area_cm2_percentile_01": norm["log_net_area_cm2_percentile_01"],
            "log_net_aspect_ratio": norm["log_net_aspect_ratio"],
        })
    metadata = {
        b"smk.web_catalog_version": b"1.0.0",
        b"smk.artworks_sha256": sha256_file(artworks_path).encode(),
        b"smk.weighted_features_sha256": sha256_file(features_path).encode(),
    }
    output = root / "data" / "processed" / "web-catalog-v1.parquet"
    table = pa.Table.from_pylist(rows).replace_schema_metadata(metadata)
    pq.write_table(table, output, compression="zstd", version="2.6", write_statistics=True)
    profile_path = root / "data" / "processed" / "sonification-profiles-v1.json"
    profile_path.write_text(json.dumps(profile_manifest(sha256_file(features_path)), indent=2) + "\n", encoding="utf-8")
    return {"rows": len(rows), "catalog_sha256": sha256_file(output),
            "sonification_profiles_sha256": sha256_file(profile_path)}

"""Deterministic exact similarity search with explainable component distances."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

PROFILE_ALIASES = {
    "color": "color-similarity-v1",
    "visual": "visual-character-similarity-v1",
    "geometry": "geometry-similarity-v1",
}


def _component_raw(left: dict[str, Any], right: dict[str, Any], component: dict[str, Any]) -> float | None:
    fields = component["fields"]
    values = [(left.get(field), right.get(field)) for field in fields]
    if any(x is None or y is None for x, y in values):
        return None
    if component["metric"] == "euclidean":
        return math.sqrt(math.fsum((float(x) - float(y)) ** 2 for x, y in values))
    return abs(float(values[0][0]) - float(values[0][1]))


def compare(left: dict[str, Any], right: dict[str, Any], profile: dict[str, Any],
            weight_overrides: dict[str, float] | None = None) -> dict[str, Any] | None:
    """Compare two rows, returning normalized contributions that sum to total distance."""
    required = profile["required_features"]
    if any(left.get(field) is None or right.get(field) is None for field in required):
        return None
    active: list[tuple[str, float, float, float]] = []
    overrides = weight_overrides or {}
    for component in profile["components"]:
        raw = _component_raw(left, right, component)
        if raw is None:
            continue
        scale = float(component["scale"])
        scaled = min(raw / scale, 1.0) if scale > 0 else 0.0
        weight = float(overrides.get(component["name"], component["weight"]))
        active.append((component["name"], raw, scaled, weight))
    active_weight_sum = math.fsum(item[3] for item in active)
    if active_weight_sum <= 0:
        return None
    components = {
        name: {
            "raw_distance": raw,
            "scaled_distance": scaled,
            "weight": weight,
            "contribution": weight * scaled / active_weight_sum,
        }
        for name, raw, scaled, weight in active
    }
    return {
        "total_distance": math.fsum(item["contribution"] for item in components.values()),
        "active_weight_sum": active_weight_sum,
        "active_components": list(components),
        "components": components,
    }


def _first_title(value: str | None) -> str | None:
    if not value:
        return None
    try:
        items = json.loads(value)
    except json.JSONDecodeError:
        return None
    for item in items or []:
        title = item.get("title") if isinstance(item, dict) else None
        if title:
            return str(title)
    return None


class SimilarityEngine:
    """In-memory exact engine for the 27k-row frozen corpus."""

    def __init__(self, root: Path):
        self.root = root
        profile_path = root / "data" / "processed" / "similarity-profiles-v1.json"
        payload = json.loads(profile_path.read_text(encoding="utf-8"))
        self.profiles = payload["profiles"]
        normalized_path = root / "data" / "processed" / "artwork-normalized-features-v1.parquet"
        self.rows = pq.read_table(normalized_path).to_pylist()
        self.by_id = {row["smk_entity_id"]: row for row in self.rows}
        self.by_object_number: dict[str, list[dict[str, Any]]] = {}
        for row in self.rows:
            self.by_object_number.setdefault(row["object_number"], []).append(row)
        canonical_path = root / "data" / "processed" / "artworks.parquet"
        title_table = pq.read_table(
            canonical_path, columns=["smk_entity_id", "titles_da_json", "titles_en_json"]
        )
        self.titles = {}
        for row in title_table.to_pylist():
            self.titles[row["smk_entity_id"]] = (
                _first_title(row["titles_da_json"]) or _first_title(row["titles_en_json"])
            )

    def profile(self, name: str) -> dict[str, Any]:
        canonical = PROFILE_ALIASES.get(name, name)
        if canonical not in self.profiles:
            raise ValueError(f"Unknown similarity profile: {name}")
        return self.profiles[canonical]

    def resolve(self, *, smk_entity_id: str | None = None,
                object_number: str | None = None) -> dict[str, Any]:
        if smk_entity_id:
            if smk_entity_id not in self.by_id:
                raise ValueError(f"Unknown corpus entity ID: {smk_entity_id}")
            return self.by_id[smk_entity_id]
        if not object_number:
            raise ValueError("Provide an object number or --id")
        matches = self.by_object_number.get(object_number, [])
        if not matches:
            raise ValueError(f"Object number is not in the frozen corpus: {object_number}")
        if len(matches) > 1:
            ids = ", ".join(sorted(row["smk_entity_id"] for row in matches))
            raise ValueError(f"Ambiguous object number {object_number}; use --id. Candidates: {ids}")
        return matches[0]

    def search_row(self, query: dict[str, Any], profile_name: str, limit: int = 10,
                   include_self: bool = False,
                   weight_overrides: dict[str, float] | None = None) -> list[dict[str, Any]]:
        profile = self.profile(profile_name)
        if any(query.get(field) is None for field in profile["required_features"]):
            raise ValueError(f"Query is not eligible for {profile['name']}")
        matches = []
        for candidate in self.rows:
            if not include_self and candidate["smk_entity_id"] == query["smk_entity_id"]:
                continue
            result = compare(query, candidate, profile, weight_overrides)
            if result is None:
                continue
            matches.append({
                "smk_entity_id": candidate["smk_entity_id"],
                "object_number": candidate["object_number"],
                "title": self.titles.get(candidate["smk_entity_id"]),
                "quality_flags": candidate["quality_flags"],
                **result,
            })
        matches.sort(key=lambda item: (item["total_distance"], item["smk_entity_id"]))
        for rank, item in enumerate(matches[:limit], 1):
            item["rank"] = rank
        return matches[:limit]

    def search(self, *, profile_name: str, limit: int = 10,
               smk_entity_id: str | None = None, object_number: str | None = None,
               include_self: bool = False) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        query = self.resolve(smk_entity_id=smk_entity_id, object_number=object_number)
        return query, self.search_row(query, profile_name, limit, include_self)


"""Build frozen enrichment-backed weighted palettes, v2 features, and similarity."""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
import time
from collections import Counter
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from smk_playground.enrichment.fetch import ENDPOINT, corpus_targets, status
from smk_playground.enrichment.weighted import (
    palette_transport_distance,
    parse_weighted_palette,
    weighted_features,
)
from smk_playground.normalize.milestone4 import linear_quantile, sha256_file
from smk_playground.similarity.engine import SimilarityEngine

ENRICHMENT_SCHEMA_VERSION = "1.0.0"
WEIGHTED_FEATURE_SCHEMA_VERSION = "2.0.0"
WEIGHTED_EXTRACTOR_VERSION = "1.0.0"
WEIGHTED_PROFILE = "weighted-color-similarity-v1"
PAIR_SEED = 20261009
PAIR_COUNT = 10_000
WEIGHTS = {
    "weighted_centroid_oklab": 0.30,
    "palette_transport_distance_oklab": 0.40,
    "weighted_palette_spread": 0.12,
    "weighted_chroma_stddev": 0.08,
    "weighted_hue_concentration": 0.05,
    "dominant_color_weight": 0.05,
}


def _colorextractor(response: Any) -> dict[str, Any] | None:
    if not isinstance(response, list):
        return None
    matches = [item for item in response if isinstance(item, dict) and item.get("type") == "colorextractor"]
    if not matches:
        return None
    return max(matches, key=lambda item: str(item.get("data", {}).get("_version_", "")))


def _profile(values: list[float]) -> dict[str, Any]:
    if not values:
        return {key: None for key in ("min", "median", "p75", "p90", "p95", "p99", "max")} | {"count": 0}
    return {"count": len(values), "min": min(values), "median": statistics.median(values),
            "p75": linear_quantile(values, 0.75), "p90": linear_quantile(values, 0.90),
            "p95": linear_quantile(values, 0.95), "p99": linear_quantile(values, 0.99),
            "max": max(values)}


def _robust(value: float | None, bounds: tuple[float, float] | None) -> float | None:
    if value is None or bounds is None:
        return None
    low, high = bounds
    if low == high:
        return None
    return min(1.0, max(0.0, (value - low) / (high - low)))


def _sample_pairs(count: int, size: int) -> list[tuple[int, int]]:
    total = min(count, size * (size - 1) // 2)
    rng = random.Random(PAIR_SEED)
    pairs: set[tuple[int, int]] = set()
    while len(pairs) < total:
        left, right = rng.randrange(size), rng.randrange(size)
        if left != right:
            pairs.add((min(left, right), max(left, right)))
    return sorted(pairs)


def _centroid_distance(left: dict[str, Any], right: dict[str, Any]) -> float:
    return math.sqrt(math.fsum(
        (left[field] - right[field]) ** 2 for field in ("centroid_l", "centroid_a", "centroid_b")
    ))


def compare_weighted(
    left: dict[str, Any], right: dict[str, Any], left_palette: list[dict[str, Any]],
    right_palette: list[dict[str, Any]], profile: dict[str, Any],
) -> dict[str, Any]:
    raw = {
        "weighted_centroid_oklab": _centroid_distance(left, right),
        "palette_transport_distance_oklab": palette_transport_distance(left_palette, right_palette),
        "weighted_palette_spread": abs(left["palette_spread_robust_01"] - right["palette_spread_robust_01"]),
        "weighted_chroma_stddev": abs(left["chroma_stddev_robust_01"] - right["chroma_stddev_robust_01"]),
        "dominant_color_weight": abs(left["dominant_color_weight_robust_01"] - right["dominant_color_weight_robust_01"]),
    }
    if left["hue_concentration_01"] is not None and right["hue_concentration_01"] is not None:
        raw["weighted_hue_concentration"] = abs(
            left["hue_concentration_01"] - right["hue_concentration_01"]
        )
    components = {}
    active_weight = math.fsum(profile["weights"][name] for name in raw)
    for name, value in raw.items():
        scaled = min(value / profile["scales"][name], 1.0)
        contribution = profile["weights"][name] * scaled / active_weight
        components[name] = {"raw_distance": value, "scaled_distance": scaled,
                            "weight": profile["weights"][name], "contribution": contribution}
    return {"total_distance": math.fsum(item["contribution"] for item in components.values()),
            "active_weight_sum": active_weight, "active_components": list(components),
            "components": components}


class WeightedSimilarityEngine:
    def __init__(self, root: Path):
        self.root = root
        payload = json.loads((root / "data" / "processed" / "similarity-profiles-v2.json").read_text(encoding="utf-8"))
        self.profile = payload["profiles"][WEIGHTED_PROFILE]
        self.rows = [row for row in pq.read_table(
            root / "data" / "processed" / "artwork-visual-features-v2.parquet"
        ).to_pylist() if row["has_weighted_palette_v1"]]
        palette_rows = pq.read_table(
            root / "data" / "processed" / "artwork-weighted-palettes-v1.parquet"
        ).to_pylist()
        self.palettes: dict[str, list[dict[str, Any]]] = {}
        for row in palette_rows:
            self.palettes.setdefault(row["smk_entity_id"], []).append(row)
        for values in self.palettes.values():
            values.sort(key=lambda row: row["palette_rank"])
        self.by_id = {row["smk_entity_id"]: row for row in self.rows}
        self.by_number: dict[str, list[dict[str, Any]]] = {}
        for row in self.rows:
            self.by_number.setdefault(row["object_number"], []).append(row)
        base = SimilarityEngine(root)
        self.titles = base.titles

    def resolve(self, object_number: str | None = None, smk_entity_id: str | None = None) -> dict[str, Any]:
        if smk_entity_id:
            if smk_entity_id not in self.by_id:
                raise ValueError(f"Entity is not weighted-palette eligible: {smk_entity_id}")
            return self.by_id[smk_entity_id]
        matches = self.by_number.get(object_number or "", [])
        if not matches:
            raise ValueError(f"Object number is not weighted-palette eligible: {object_number}")
        if len(matches) > 1:
            raise ValueError(f"Ambiguous object number {object_number}; use --id")
        return matches[0]

    def search_row(self, query: dict[str, Any], limit: int = 10,
                   include_self: bool = False) -> list[dict[str, Any]]:
        output = []
        query_palette = self.palettes[query["smk_entity_id"]]
        for candidate in self.rows:
            if not include_self and candidate["smk_entity_id"] == query["smk_entity_id"]:
                continue
            result = compare_weighted(
                query, candidate, query_palette, self.palettes[candidate["smk_entity_id"]], self.profile
            )
            output.append({"smk_entity_id": candidate["smk_entity_id"],
                           "object_number": candidate["object_number"],
                           "title": self.titles.get(candidate["smk_entity_id"]), **result})
        output.sort(key=lambda row: (row["total_distance"], row["smk_entity_id"]))
        for rank, row in enumerate(output[:limit], 1):
            row["rank"] = rank
        return output[:limit]


def run(root: Path) -> dict[str, Any]:
    fetch_status = status(root)
    targets, entity_mapping = corpus_targets(root)
    state = json.loads((root / "data" / "raw" / "enrichment" / "fetch-state-v1.json").read_text(encoding="utf-8"))
    v1_path = root / "data" / "processed" / "artwork-visual-features-v1.parquet"
    palette_v1_path = root / "data" / "processed" / "artwork-palettes-v1.parquet"
    normalized_v1_path = root / "data" / "processed" / "artwork-normalized-features-v1.parquet"
    v1_hashes = {path.name: sha256_file(path) for path in (v1_path, palette_v1_path, normalized_v1_path)}
    v1_rows = pq.read_table(v1_path).to_pylist()
    v1_by_id = {row["smk_entity_id"]: row for row in v1_rows}
    bulk_palettes: dict[str, set[str]] = {}
    bulk_palette_order: dict[str, list[tuple[int, str]]] = {}
    for row in pq.read_table(
        palette_v1_path, columns=["smk_entity_id", "palette_rank", "hex"]
    ).to_pylist():
        bulk_palettes.setdefault(row["smk_entity_id"], set()).add(row["hex"])
        bulk_palette_order.setdefault(row["smk_entity_id"], []).append(
            (row["palette_rank"], row["hex"])
        )

    manifest_entries = []
    palettes_by_entity: dict[str, list[dict[str, Any]]] = {}
    palette_rows = []
    comparison_rows = []
    feature_rows = []
    outcome_counts = Counter()
    status_counts = Counter()
    component_counts = Counter()
    version_counts = Counter()
    versions_by_component: dict[str, set[str]] = {}
    token_counts = []
    unique_counts = []
    for target_index, object_number in enumerate(targets, 1):
        state_record = state.get("records", {}).get(object_number)
        if not state_record:
            outcome_counts["not_requested"] += 1
            continue
        cache_path = Path(state_record["cache_path"])
        if not cache_path.is_absolute():
            cache_path = root / cache_path
        source = json.loads(cache_path.read_text(encoding="utf-8"))
        outcome_counts[source["outcome"]] += 1
        response = source.get("response_json")
        if isinstance(response, list):
            for component in response:
                if isinstance(component, dict):
                    component_type = str(component.get("type"))
                    version = str((component.get("data") or {}).get("_version_"))
                    component_counts[component_type] += 1
                    version_counts[f"{component_type}:{version}"] += 1
                    versions_by_component.setdefault(component_type, set()).add(version)
        extractor = _colorextractor(response)
        data = extractor.get("data", {}) if extractor else {}
        raw = data.get("colors_palette_weighted_s")
        parsed, audit = parse_weighted_palette(raw)
        status_counts[audit["status"]] += 1
        if audit["valid_token_count"]:
            token_counts.append(audit["valid_token_count"])
            unique_counts.append(audit["unique_color_count"])
        raw_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest() if isinstance(raw, str) else None
        manifest_entries.append({
            "object_number": object_number, "smk_entity_ids": entity_mapping[object_number],
            "response_timestamp": source.get("response_at_utc"), "http_status": source.get("http_status"),
            "outcome": source["outcome"], "source_endpoint": source["endpoint"],
            "cache_path": state_record["cache_path"], "colorextractor_version": data.get("_version_"),
            "weighted_palette_raw_sha256": raw_hash, "weighted_palette_status": audit["status"],
            "token_count": audit["valid_token_count"], "unique_color_count": audit["unique_color_count"],
        })
        for entity_id in entity_mapping[object_number]:
            base = v1_by_id[entity_id]
            status_value = audit["status"] if source["outcome"] == "success" else source["outcome"]
            if parsed:
                entity_palette = []
                for item in parsed:
                    record = {"smk_entity_id": entity_id, "object_number": object_number,
                              "palette_source": "smk_enrichment", "palette_schema_version": "1.0.0",
                              "palette_weighting": "enrichment_token_frequency",
                              "enrichment_component": "colorextractor",
                              "enrichment_version": str(data.get("_version_")), **item}
                    palette_rows.append(record)
                    entity_palette.append(record)
                palettes_by_entity[entity_id] = entity_palette
                calculated = weighted_features(entity_palette)
                bulk_set = bulk_palettes[entity_id]
                enrichment_set = {row["hex"] for row in entity_palette}
                intersection = bulk_set & enrichment_set
                comparison_rows.append({
                    "smk_entity_id": entity_id, "object_number": object_number,
                    "exact_same_color_set": bulk_set == enrichment_set,
                    "partial_overlap": bool(intersection) and bulk_set != enrichment_set,
                    "no_overlap": not intersection, "bulk_palette_size": len(bulk_set),
                    "enrichment_palette_size": len(enrichment_set),
                    "different_palette_size": len(bulk_set) != len(enrichment_set),
                    "enrichment_only_colors": sorted(enrichment_set - bulk_set),
                    "bulk_only_colors": sorted(bulk_set - enrichment_set),
                    "order_differs": [row["hex"] for row in entity_palette]
                    != [value[1] for value in sorted(bulk_palette_order[entity_id])],
                })
            else:
                calculated = {key: None for key in (
                    "centroid_l", "centroid_a", "centroid_b", "centroid_chroma", "centroid_hue_deg",
                    "palette_entropy", "palette_entropy_01", "effective_palette_size",
                    "palette_spread_oklab", "lightness_stddev", "chroma_stddev",
                    "hue_concentration_01", "dominant_color_weight", "dominant_color_hex")}
                calculated["feature_quality_flags"] = ["WEIGHTED_PALETTE_UNAVAILABLE"]
            feature_rows.append({
                "smk_entity_id": entity_id, "object_number": object_number,
                "feature_schema": "artart-visual-features", "feature_schema_version": WEIGHTED_FEATURE_SCHEMA_VERSION,
                "extractor_version": WEIGHTED_EXTRACTOR_VERSION, "bulk_feature_lineage_sha256": v1_hashes[v1_path.name],
                "palette_source": "smk_enrichment", "palette_weighting": "enrichment_token_frequency",
                "enrichment_component": "colorextractor" if extractor else None,
                "enrichment_version": str(data.get("_version_")) if extractor else None,
                "has_weighted_palette_v1": bool(parsed), "weighted_palette_status": status_value,
                "weighted_palette_token_count": audit["valid_token_count"],
                "weighted_palette_unique_color_count": audit["unique_color_count"],
                **calculated,
                "centroid_shift_from_v1_oklab": math.sqrt(math.fsum(
                    (calculated[field] - base[field]) ** 2
                    for field in ("centroid_l", "centroid_a", "centroid_b")
                )) if parsed else None,
                "hue_concentration_shift_from_v1": (
                    calculated["hue_concentration_01"] - base["hue_concentration_01"]
                    if parsed and calculated["hue_concentration_01"] is not None
                    and base["hue_concentration_01"] is not None else None
                ),
            })
        if target_index % 1_000 == 0:
            print(f"Loaded enrichment cache: {target_index}/{len(targets)} object numbers", flush=True)

    # Ensure every corpus entity remains represented even when an object number was not fetched.
    represented = {row["smk_entity_id"] for row in feature_rows}
    for base in v1_rows:
        if base["smk_entity_id"] not in represented:
            feature_rows.append({
                "smk_entity_id": base["smk_entity_id"], "object_number": base["object_number"],
                "feature_schema": "artart-visual-features", "feature_schema_version": WEIGHTED_FEATURE_SCHEMA_VERSION,
                "extractor_version": WEIGHTED_EXTRACTOR_VERSION, "bulk_feature_lineage_sha256": v1_hashes[v1_path.name],
                "palette_source": "smk_enrichment", "palette_weighting": "enrichment_token_frequency",
                "enrichment_component": None, "enrichment_version": None,
                "has_weighted_palette_v1": False, "weighted_palette_status": "not_requested",
                "weighted_palette_token_count": 0, "weighted_palette_unique_color_count": 0,
                **{key: None for key in (
                    "centroid_l", "centroid_a", "centroid_b", "centroid_chroma", "centroid_hue_deg",
                    "palette_entropy", "palette_entropy_01", "effective_palette_size",
                    "palette_spread_oklab", "lightness_stddev", "chroma_stddev", "hue_concentration_01",
                    "dominant_color_weight", "dominant_color_hex", "centroid_shift_from_v1_oklab",
                    "hue_concentration_shift_from_v1")},
                "feature_quality_flags": ["WEIGHTED_PALETTE_UNAVAILABLE"],
            })
    feature_rows.sort(key=lambda row: row["smk_entity_id"])
    palette_rows.sort(key=lambda row: (row["smk_entity_id"], row["palette_rank"]))
    comparison_rows.sort(key=lambda row: row["smk_entity_id"])

    valid_features = [row for row in feature_rows if row["has_weighted_palette_v1"]]
    normalization_values = {
        "palette_spread_oklab": [row["palette_spread_oklab"] for row in valid_features],
        "chroma_stddev": [row["chroma_stddev"] for row in valid_features],
        "dominant_color_weight": [row["dominant_color_weight"] for row in valid_features],
    }
    normalization_bounds = {
        key: (linear_quantile(values, 0.01), linear_quantile(values, 0.99))
        if values else None
        for key, values in normalization_values.items()
    }
    for row in feature_rows:
        row["palette_spread_robust_01"] = _robust(
            row["palette_spread_oklab"], normalization_bounds["palette_spread_oklab"]
        )
        row["chroma_stddev_robust_01"] = _robust(
            row["chroma_stddev"], normalization_bounds["chroma_stddev"]
        )
        row["dominant_color_weight_robust_01"] = _robust(
            row["dominant_color_weight"], normalization_bounds["dominant_color_weight"]
        )

    manifest = {
        "manifest_version": ENRICHMENT_SCHEMA_VERSION, "source_endpoint": ENDPOINT,
        "generated_at_utc": max(
            (entry["response_timestamp"] for entry in manifest_entries if entry["response_timestamp"]),
            default=None,
        ),
        "corpus_version": "smk-public-visual-v1", "corpus_entity_count": len(v1_rows),
        "unique_object_number_count": len(targets),
        "duplicate_object_number_groups": sum(len(ids) > 1 for ids in entity_mapping.values()),
        "fetch_status": fetch_status, "records": manifest_entries,
    }
    manifest_path = root / "data" / "processed" / "enrichment-source-manifest-v1.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest_hash = sha256_file(manifest_path)
    for row in feature_rows:
        row["enrichment_source_manifest_sha256"] = manifest_hash
    metadata = {b"smk.enrichment_manifest_sha256": manifest_hash.encode(),
                b"smk.palette_weighting": b"enrichment_token_frequency"}
    def write(rows: list[dict[str, Any]], path: Path) -> None:
        table = pa.Table.from_pylist(rows).replace_schema_metadata(metadata)
        pq.write_table(table, path, compression="zstd", version="2.6", write_statistics=True)
    weighted_palette_path = root / "data" / "processed" / "artwork-weighted-palettes-v1.parquet"
    feature_v2_path = root / "data" / "processed" / "artwork-visual-features-v2.parquet"
    comparison_path = root / "data" / "reports" / "enrichment-palette-comparison-v1.parquet"
    write(palette_rows, weighted_palette_path)
    write(feature_rows, feature_v2_path)
    write(comparison_rows, comparison_path)

    pairs = _sample_pairs(PAIR_COUNT, len(valid_features))
    component_values = {name: [] for name in WEIGHTS}
    for left_index, right_index in pairs:
        left, right = valid_features[left_index], valid_features[right_index]
        component_values["weighted_centroid_oklab"].append(_centroid_distance(left, right))
        component_values["palette_transport_distance_oklab"].append(palette_transport_distance(
            palettes_by_entity[left["smk_entity_id"]], palettes_by_entity[right["smk_entity_id"]]
        ))
        component_values["weighted_palette_spread"].append(abs(left["palette_spread_robust_01"] - right["palette_spread_robust_01"]))
        component_values["weighted_chroma_stddev"].append(abs(left["chroma_stddev_robust_01"] - right["chroma_stddev_robust_01"]))
        component_values["dominant_color_weight"].append(abs(left["dominant_color_weight_robust_01"] - right["dominant_color_weight_robust_01"]))
        if left["hue_concentration_01"] is not None and right["hue_concentration_01"] is not None:
            component_values["weighted_hue_concentration"].append(abs(left["hue_concentration_01"] - right["hue_concentration_01"]))
    distributions = {name: _profile(values) for name, values in component_values.items()}
    profile = {
        "name": WEIGHTED_PROFILE, "profile_version": "1.0.0",
        "required_features": ["weighted palette", "weighted centroid", "weighted spread", "weighted chroma stddev", "dominant weight"],
        "optional_features": ["weighted hue concentration"], "weights": WEIGHTS,
        "scales": {name: values["p95"] for name, values in distributions.items()},
        "scale_rule": f"P95 over {len(pairs)} deterministic eligible pairs, seed {PAIR_SEED}",
        "missing_value_behavior": "weighted palette required; hue concentration omitted and active weights renormalized",
        "distance_semantics": "weighted mean of P95-scaled component distances clipped to [0,1]; lower is more similar",
        "tie_breaking": ["total_distance ascending", "smk_entity_id ascending"],
    }
    profiles_payload = {
        "profile_set_version": "2.0.0", "additive_to_similarity_profiles_v1": True,
        "input_hashes": {"enrichment_manifest": manifest_hash,
                         "weighted_palettes": sha256_file(weighted_palette_path),
                         "weighted_features_v2": sha256_file(feature_v2_path), **v1_hashes},
        "calibration_distributions": distributions, "profiles": {WEIGHTED_PROFILE: profile},
    }
    profiles_path = root / "data" / "processed" / "similarity-profiles-v2.json"
    profiles_path.write_text(json.dumps(profiles_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    engine = WeightedSimilarityEngine(root)
    kms = engine.resolve(object_number="KMS8892")
    started = time.perf_counter()
    weighted_matches = engine.search_row(kms, 10)
    query_seconds = time.perf_counter() - started
    base_engine = SimilarityEngine(root)
    base_query = base_engine.resolve(object_number="KMS8892")
    base_full = base_engine.search_row(base_query, "color", len(base_engine.rows))
    base_matches = base_full[:10]
    base_ranks = {row["smk_entity_id"]: row["rank"] for row in base_full}
    base_ids = [row["smk_entity_id"] for row in base_matches]
    weighted_ids = [row["smk_entity_id"] for row in weighted_matches]
    kms_palette = palettes_by_entity[kms["smk_entity_id"]]
    summary = {
        "fetch": fetch_status, "outcome_counts": dict(sorted(outcome_counts.items())),
        "weighted_palette_status_counts": dict(sorted(status_counts.items())),
        "component_distribution": dict(sorted(component_counts.items())),
        "component_version_distinct_count": len(version_counts),
        "distinct_versions_by_component": {
            key: len(value) for key, value in sorted(versions_by_component.items())
        },
        "weighted_palette_entity_count": len(valid_features),
        "suspicious_pattern_counts": {
            "single_unique_color": sum(row["weighted_palette_unique_color_count"] == 1 for row in valid_features),
            "dominant_weight_gte_0_9": sum(row["dominant_color_weight"] >= 0.9 for row in valid_features),
            "one_token_per_color": sum(
                row["weighted_palette_token_count"] == row["weighted_palette_unique_color_count"]
                for row in valid_features
            ),
        },
        "token_count_distribution": _profile(token_counts),
        "unique_color_count_distribution": _profile(unique_counts),
        "bulk_palette_comparison": {
            "exact_same_color_set": sum(row["exact_same_color_set"] for row in comparison_rows),
            "partial_overlap": sum(row["partial_overlap"] for row in comparison_rows),
            "no_overlap": sum(row["no_overlap"] for row in comparison_rows),
            "different_palette_size": sum(row["different_palette_size"] for row in comparison_rows),
            "order_differs": sum(row["order_differs"] for row in comparison_rows),
        },
        "feature_distributions": {name: _profile([row[name] for row in valid_features if row[name] is not None])
                                  for name in ("dominant_color_weight", "palette_entropy", "palette_entropy_01",
                                               "effective_palette_size", "palette_spread_oklab",
                                               "centroid_shift_from_v1_oklab", "hue_concentration_shift_from_v1")},
        "palette_transport_calibration": distributions["palette_transport_distance_oklab"],
        "weighted_profile": profile, "kms8892": {
            "bulk_palette": v1_by_id[kms["smk_entity_id"]]["source_palette"],
            "weighted_palette": [{key: row[key] for key in ("hex", "token_count", "weight")}
                                 for row in kms_palette],
            "weighted_features": {key: kms[key] for key in (
                "centroid_l", "centroid_a", "centroid_b", "centroid_chroma", "centroid_hue_deg",
                "dominant_color_hex", "dominant_color_weight", "palette_entropy",
                "palette_entropy_01", "effective_palette_size", "palette_spread_oklab",
                "hue_concentration_01")},
            "weighted_top10": weighted_matches, "bulk_color_top10": base_matches,
            "top10_overlap_count": len(set(base_ids) & set(weighted_ids)),
            "newly_promoted_ids": [value for value in weighted_ids if value not in base_ids],
            "demoted_ids": [value for value in base_ids if value not in weighted_ids],
            "weighted_top10_ranks_under_bulk_color": [
                {"smk_entity_id": value, "bulk_color_rank": base_ranks[value]}
                for value in weighted_ids
            ],
            "weighted_top10_retained_by_bulk_candidate_cutoffs": {
                str(cutoff): sum(base_ranks[value] <= cutoff for value in weighted_ids)
                for cutoff in (200, 500, 1000)
            },
        },
        "performance": {"weighted_exact_full_corpus_query_seconds": query_seconds,
                        "eligible_entities": len(valid_features)},
        "v1_hashes_verified_unchanged": v1_hashes,
    }
    report = root / "data" / "reports" / "enrichment-summary-v1.json"
    report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    weighted_report = root / "data" / "reports" / "weighted-similarity-summary-v1.json"
    weighted_report.write_text(json.dumps({key: summary[key] for key in (
        "palette_transport_calibration", "weighted_profile", "kms8892", "performance")},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary

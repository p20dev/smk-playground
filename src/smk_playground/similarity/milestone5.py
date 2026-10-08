"""Build Milestone 5 similarity profiles, diagnostics, and QA examples."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import time
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from smk_playground.normalize.milestone4 import linear_quantile, sha256_file
from smk_playground.similarity.engine import SimilarityEngine, compare

PROFILE_VERSION = "1.0.0"
PAIR_SEED = 20261008
CALIBRATION_PAIR_COUNT = 500_000
PERSISTED_PAIRS_PER_PROFILE = 50_000

COMPONENT_FIELDS = {
    "centroid_oklab": (["centroid_l", "centroid_a", "centroid_b"], "euclidean"),
    "palette_spread": (["palette_spread_oklab_robust_01"], "absolute"),
    "chroma_stddev": (["chroma_stddev_robust_01"], "absolute"),
    "hue_concentration": (["hue_concentration_01"], "absolute"),
    "brightness": (["smk_brightness_robust_01"], "absolute"),
    "contrast": (["smk_contrast_robust_01"], "absolute"),
    "saturation": (["smk_saturation_robust_01"], "absolute"),
    "entropy": (["smk_entropy_robust_01"], "absolute"),
    "log_width": (["log_net_width_cm_robust_01"], "absolute"),
    "log_height": (["log_net_height_cm_robust_01"], "absolute"),
    "log_area": (["log_net_area_cm2_robust_01"], "absolute"),
    "log_aspect": (["log_net_aspect_ratio_robust_01"], "absolute"),
}

WEIGHTS = {
    "color-similarity-v1": {
        "centroid_oklab": 0.65, "palette_spread": 0.20,
        "chroma_stddev": 0.10, "hue_concentration": 0.05,
    },
    "visual-character-similarity-v1": {
        "centroid_oklab": 0.45, "palette_spread": 0.12, "chroma_stddev": 0.08,
        "hue_concentration": 0.03, "brightness": 0.10, "contrast": 0.05,
        "saturation": 0.10, "entropy": 0.07,
    },
    "geometry-similarity-v1": {
        "log_width": 0.20, "log_height": 0.20, "log_area": 0.35, "log_aspect": 0.25,
    },
}


def _sample_pairs(size: int, count: int, seed: int) -> list[tuple[int, int]]:
    rng = random.Random(seed)
    pairs: set[tuple[int, int]] = set()
    while len(pairs) < count:
        left = rng.randrange(size)
        right = rng.randrange(size - 1)
        if right >= left:
            right += 1
        pairs.add((min(left, right), max(left, right)))
    return sorted(pairs)


def _raw_component(left: dict[str, Any], right: dict[str, Any], name: str) -> float | None:
    fields, metric = COMPONENT_FIELDS[name]
    values = [(left.get(field), right.get(field)) for field in fields]
    if any(x is None or y is None for x, y in values):
        return None
    if metric == "euclidean":
        return math.sqrt(math.fsum((float(x) - float(y)) ** 2 for x, y in values))
    return abs(float(values[0][0]) - float(values[0][1]))


def _distribution(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values), "median": statistics.median(values),
        "p75": linear_quantile(values, 0.75), "p90": linear_quantile(values, 0.90),
        "p95": linear_quantile(values, 0.95), "p99": linear_quantile(values, 0.99),
    }


def _profiles(root: Path, rows: list[dict[str, Any]], pairs: list[tuple[int, int]]) -> tuple[dict[str, Any], dict[str, Any]]:
    samples = {name: [] for name in COMPONENT_FIELDS}
    for left_index, right_index in pairs:
        left, right = rows[left_index], rows[right_index]
        for name, sample_values in samples.items():
            value = _raw_component(left, right, name)
            if value is not None:
                sample_values.append(value)
    distributions = {name: _distribution(values) for name, values in samples.items()}
    scales = {name: values["p95"] for name, values in distributions.items()}
    normalized_path = root / "data" / "processed" / "artwork-normalized-features-v1.parquet"
    features_path = root / "data" / "processed" / "artwork-visual-features-v1.parquet"
    normalization_path = root / "data" / "processed" / "normalization-profile-v1.json"
    normalization = json.loads(normalization_path.read_text(encoding="utf-8"))

    required = {
        "color-similarity-v1": ["centroid_l", "centroid_a", "centroid_b",
                                "palette_spread_oklab_robust_01", "chroma_stddev_robust_01"],
        "visual-character-similarity-v1": ["centroid_l", "centroid_a", "centroid_b",
                                           "palette_spread_oklab_robust_01", "chroma_stddev_robust_01"],
        "geometry-similarity-v1": ["log_net_width_cm_robust_01", "log_net_height_cm_robust_01",
                                   "log_net_area_cm2_robust_01", "log_net_aspect_ratio_robust_01"],
    }
    optional = {
        "color-similarity-v1": ["hue_concentration_01"],
        "visual-character-similarity-v1": ["hue_concentration_01", "smk_brightness_robust_01",
                                            "smk_contrast_robust_01", "smk_saturation_robust_01",
                                            "smk_entropy_robust_01"],
        "geometry-similarity-v1": [],
    }
    profiles = {}
    for name, weights in WEIGHTS.items():
        profiles[name] = {
            "name": name, "profile_version": PROFILE_VERSION,
            "required_features": required[name], "optional_features": optional[name],
            "components": [
                {"name": component, "fields": COMPONENT_FIELDS[component][0],
                 "metric": COMPONENT_FIELDS[component][1], "transform": "raw OKLab" if component == "centroid_oklab" else "robust_01/natural_01 absolute difference",
                 "scale": scales[component], "scale_rule": "deterministic pair-sample P95",
                 "weight": weight}
                for component, weight in weights.items()
            ],
            "missing_value_behavior": "required missing => ineligible; optional missing on either side => omit and renormalize active weights",
            "distance_semantics": "weighted mean of P95-scaled component distances clipped to [0,1]; lower is more similar",
            "tie_breaking": ["total_distance ascending", "smk_entity_id ascending"],
        }
    payload = {
        "profile_set_version": PROFILE_VERSION,
        "generated_at_utc": normalization["generated_at_utc"],
        "corpus_version": normalization["corpus_version"],
        "normalization_profile": normalization["normalization_profile"],
        "normalization_version": normalization["normalization_version"],
        "input_hashes": {
            "artwork_visual_features_v1_sha256": sha256_file(features_path),
            "artwork_normalized_features_v1_sha256": sha256_file(normalized_path),
            "normalization_profile_v1_sha256": sha256_file(normalization_path),
        },
        "calibration": {"seed": PAIR_SEED, "distinct_pair_count": len(pairs),
                        "component_distributions": distributions},
        "profiles": profiles,
    }
    return payload, distributions


def _eligible_count(rows: list[dict[str, Any]], profile: dict[str, Any]) -> int:
    return sum(all(row.get(field) is not None for field in profile["required_features"]) for row in rows)


def _profile_pair_rows(rows: list[dict[str, Any]], pairs: list[tuple[int, int]],
                       profiles: dict[str, Any]) -> list[dict[str, Any]]:
    output = []
    for profile_name, profile in profiles.items():
        written = 0
        for left_index, right_index in pairs:
            result = compare(rows[left_index], rows[right_index], profile)
            if result is None:
                continue
            left, right = rows[left_index], rows[right_index]
            output.append({
                "left_smk_entity_id": left["smk_entity_id"],
                "right_smk_entity_id": right["smk_entity_id"], "profile": profile_name,
                "total_distance": result["total_distance"],
                "active_weight_sum": result["active_weight_sum"],
                "active_components": result["active_components"],
                "component_distances_json": json.dumps(result["components"], sort_keys=True, separators=(",", ":")),
            })
            written += 1
            if written >= PERSISTED_PAIRS_PER_PROFILE:
                break
    return output


def _select_qa(rows: list[dict[str, Any]]) -> list[str]:
    def entity_for(key: str, *, maximum: bool) -> str:
        valid = [row for row in rows if row.get(key) is not None]
        selected = sorted(valid, key=lambda row: (float(row[key]), row["smk_entity_id"]), reverse=maximum)[0]
        return selected["smk_entity_id"]
    incomplete = min((row for row in rows if row["smk_saturation"] is None), key=lambda row: row["smk_entity_id"])
    ids = [
        next(row["smk_entity_id"] for row in rows if row["object_number"] == "KMS8892"),
        next(row["smk_entity_id"] for row in rows if row["object_number"] == "KMS1571"),
        entity_for("centroid_chroma", maximum=True), entity_for("palette_spread_oklab", maximum=True),
        entity_for("palette_spread_oklab", maximum=False), incomplete["smk_entity_id"],
    ]
    return list(dict.fromkeys(ids))


def _stability(engine: SimilarityEngine, query_ids: list[str]) -> list[dict[str, Any]]:
    output = []
    for query_id in query_ids:
        query = engine.by_id[query_id]
        for profile_name in engine.profiles:
            profile = engine.profile(profile_name)
            if any(query.get(field) is None for field in profile["required_features"]):
                continue
            baseline = engine.search_row(query, profile_name, 10)
            baseline_ids = {item["smk_entity_id"] for item in baseline}
            for component in profile["components"]:
                for factor in (0.85, 1.15):
                    varied = engine.search_row(
                        query, profile_name, 10,
                        weight_overrides={component["name"]: component["weight"] * factor},
                    )
                    overlap = len(baseline_ids & {item["smk_entity_id"] for item in varied})
                    output.append({"query_smk_entity_id": query_id, "profile": profile_name,
                                   "component": component["name"], "factor": factor,
                                   "top10_overlap": overlap})
    return output


def _examples_markdown(engine: SimilarityEngine, qa_ids: list[str]) -> tuple[str, dict[str, Any]]:
    lines = ["# Similarity examples", "", "All statements below are deterministic feature comparisons, not aesthetic judgments.", ""]
    payload = {}
    for query_id in qa_ids:
        query = engine.by_id[query_id]
        key = query["object_number"] or query_id
        payload[key] = {}
        lines.extend([f"## {key}", "", f"Entity: `{query_id}`. Title: {engine.titles.get(query_id) or 'unavailable'}.", ""])
        query_features = {
            name: query.get(name) for name in (
                "centroid_l", "centroid_a", "centroid_b", "palette_spread_oklab",
                "chroma_stddev", "hue_concentration_01", "smk_brightness",
                "smk_contrast", "smk_saturation", "smk_entropy", "log_net_width_cm",
                "log_net_height_cm", "log_net_area_cm2", "log_net_aspect_ratio",
            )
        }
        lines.extend(["Query features:", "", f"`{json.dumps(query_features, sort_keys=True)}`", ""])
        for profile_name in engine.profiles:
            profile = engine.profile(profile_name)
            if any(query.get(field) is None for field in profile["required_features"]):
                lines.extend([f"### {profile_name}", "", "Not eligible: a required feature is null.", ""])
                continue
            results = engine.search_row(query, profile_name, 10)
            payload[key][profile_name] = results
            lines.extend([f"### {profile_name}", "", "| Rank | Object | Title | Distance | Contributions | Factual explanation |", "|---:|---|---|---:|---|---|"])
            for result in results:
                contributions = ", ".join(
                    f"{name}={part['contribution']:.4f}"
                    for name, part in result["components"].items()
                )
                centroid = result["components"].get("centroid_oklab")
                explanation = "shared normalized feature values"
                if centroid:
                    explanation = "similar centroid color" if centroid["scaled_distance"] < 0.25 else "centroid color contributes substantially"
                if "hue_concentration" not in result["active_components"] and profile_name != "geometry-similarity-v1":
                    explanation += "; hue concentration unavailable"
                title = (result["title"] or "unavailable").replace("|", "\\|")
                lines.append(f"| {result['rank']} | {result['object_number']} | {title} | {result['total_distance']:.6f} | {contributions} | {explanation} |")
            lines.append("")
    return "\n".join(lines) + "\n", payload


def run(root: Path) -> dict[str, Any]:
    normalized_path = root / "data" / "processed" / "artwork-normalized-features-v1.parquet"
    load_start = time.perf_counter()
    rows = pq.read_table(normalized_path).to_pylist()
    load_seconds = time.perf_counter() - load_start
    pairs = _sample_pairs(len(rows), CALIBRATION_PAIR_COUNT, PAIR_SEED)
    profile_payload, distributions = _profiles(root, rows, pairs)
    profile_path = root / "data" / "processed" / "similarity-profiles-v1.json"
    profile_path.write_text(json.dumps(profile_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    metadata = {
        b"smk.similarity_profile_set_version": PROFILE_VERSION.encode(),
        b"smk.similarity_profiles_sha256": hashlib.sha256(profile_path.read_bytes()).hexdigest().encode(),
    }
    pair_rows = _profile_pair_rows(rows, pairs, profile_payload["profiles"])
    pair_table = pa.Table.from_pylist(pair_rows).replace_schema_metadata(metadata)
    pq.write_table(pair_table, root / "data" / "reports" / "similarity-pair-sample-v1.parquet",
                   compression="zstd", version="2.6", write_statistics=True)

    engine_start = time.perf_counter()
    engine = SimilarityEngine(root)
    engine_load_seconds = time.perf_counter() - engine_start
    qa_ids = _select_qa(rows)
    markdown, examples = _examples_markdown(engine, qa_ids)
    (root / "docs" / "SIMILARITY_EXAMPLES.md").write_text(markdown, encoding="utf-8")
    kms = engine.resolve(object_number="KMS8892")
    calculation_times = []
    ranking_times = []
    for _ in range(5):
        start = time.perf_counter()
        unsorted = []
        profile = engine.profile("color")
        for candidate in engine.rows:
            if candidate["smk_entity_id"] == kms["smk_entity_id"]:
                continue
            result = compare(kms, candidate, profile)
            if result is not None:
                unsorted.append((result["total_distance"], candidate["smk_entity_id"]))
        calculation_times.append(time.perf_counter() - start)
        rank_start = time.perf_counter()
        unsorted.sort()
        unsorted[:10]
        ranking_times.append(time.perf_counter() - rank_start)
    stability = _stability(engine, qa_ids)
    summary = {
        "profile_set_version": PROFILE_VERSION,
        "input_hashes": profile_payload["input_hashes"],
        "eligible_counts": {name: _eligible_count(rows, profile)
                            for name, profile in profile_payload["profiles"].items()},
        "pair_calibration": {"seed": PAIR_SEED, "distinct_pair_count": len(pairs),
                             "distributions": distributions},
        "persisted_pair_rows": len(pair_rows), "qa_query_ids": qa_ids,
        "kms8892": examples["KMS8892"],
        "ranking_stability": {
            "variation": "each component weight independently multiplied by 0.85 and 1.15",
            "minimum_top10_overlap": min(item["top10_overlap"] for item in stability),
            "median_top10_overlap": statistics.median(item["top10_overlap"] for item in stability),
            "cases": stability,
        },
        "performance": {
            "direct_normalized_parquet_load_seconds": load_seconds,
            "engine_load_seconds_including_titles": engine_load_seconds,
            "exact_color_distance_calculation_seconds_median_of_5": statistics.median(calculation_times),
            "full_sort_and_top10_seconds_median_of_5": statistics.median(ranking_times),
            "exact_color_query_total_seconds_median_of_5": statistics.median(
                [calculation + ranking for calculation, ranking in zip(calculation_times, ranking_times)]
            ),
            "corpus_rows": len(rows),
        },
    }
    summary_path = root / "data" / "reports" / "similarity-summary-v1.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(run(args.root.resolve()), indent=2))


if __name__ == "__main__":
    main()

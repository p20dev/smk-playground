"""Versioned corpus statistics and normalized features for Milestone 4."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

PROFILE_NAME = "smk-public-visual-v1"
NORMALIZATION_VERSION = "1.0.0"

PROFILE_FEATURES = (
    "centroid_l", "centroid_a", "centroid_b", "centroid_chroma",
    "palette_spread_oklab", "lightness_stddev", "chroma_stddev",
    "hue_concentration_01", "palette_entropy_01", "effective_palette_size",
    "smk_brightness", "smk_contrast", "smk_saturation", "smk_entropy",
    "smk_colortemp", "net_width_cm", "net_height_cm", "net_area_cm2",
    "net_aspect_ratio", "log_net_width_cm", "log_net_height_cm",
    "log_net_area_cm2", "image_aspect_ratio", "aspect_mismatch_log",
    "log_net_aspect_ratio", "log_image_aspect_ratio",
)
NATURAL_01 = frozenset({"hue_concentration_01", "palette_entropy_01"})
PRIMARY_EXCLUSIONS = {
    "smk_colortemp": "extreme finite values and uncertain semantics",
    "palette_entropy_01": "uniform v1 palette weights make entropy non-informative",
    "effective_palette_size": "mostly duplicates analytical palette size under uniform weights",
}
FAMILIES = {
    "color_core_v1": (
        "centroid_l", "centroid_a", "centroid_b", "palette_spread_oklab_robust_01",
        "lightness_stddev_robust_01", "chroma_stddev_robust_01",
        "hue_concentration_01",
    ),
    "visual_character_v1": (
        "smk_brightness_robust_01", "smk_contrast_robust_01",
        "smk_saturation_robust_01", "smk_entropy_robust_01",
    ),
    "geometry_v1": (
        "log_net_width_cm_robust_01", "log_net_height_cm_robust_01",
        "log_net_area_cm2_robust_01", "log_net_aspect_ratio_robust_01",
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def linear_quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[low]
    fraction = position - low
    return ordered[low] * (1 - fraction) + ordered[high] * fraction


def midrank_percentiles(values: Iterable[float | None]) -> list[float | None]:
    """Return deterministic empirical midranks, scaled to [0, 1]."""
    source = list(values)
    valid = [(index, float(value)) for index, value in enumerate(source)
             if value is not None and math.isfinite(float(value))]
    result: list[float | None] = [None] * len(source)
    if not valid:
        return result
    ordered = sorted(valid, key=lambda item: (item[1], item[0]))
    denominator = max(len(ordered) - 1, 1)
    cursor = 0
    while cursor < len(ordered):
        end = cursor + 1
        while end < len(ordered) and ordered[end][1] == ordered[cursor][1]:
            end += 1
        rank = ((cursor + end - 1) / 2) / denominator if len(ordered) > 1 else 0.5
        for position in range(cursor, end):
            result[ordered[position][0]] = rank
        cursor = end
    return result


def robust_01(value: float | None, p01: float, p99: float, *, natural: bool = False) -> float | None:
    if value is None or not math.isfinite(float(value)) or p01 == p99:
        return None
    if natural:
        return min(1.0, max(0.0, float(value)))
    return min(1.0, max(0.0, (float(value) - p01) / (p99 - p01)))


def robust_z(value: float | None, median: float, mad: float) -> float | None:
    if value is None or not math.isfinite(float(value)) or mad == 0:
        return None
    return (float(value) - median) / (1.4826 * mad)


def log_aspect_ratio(width: float | None, height: float | None) -> float | None:
    if width is None or height is None or width <= 0 or height <= 0:
        return None
    return math.log(width / height)


def hue_xy(hue_degrees: float | None) -> tuple[float | None, float | None]:
    if hue_degrees is None or not math.isfinite(float(hue_degrees)):
        return None, None
    angle = math.radians(float(hue_degrees))
    return math.cos(angle), math.sin(angle)


def feature_profile(name: str, values: list[float | None]) -> dict[str, Any]:
    finite = [float(value) for value in values
              if value is not None and math.isfinite(float(value))]
    count = len(values)
    null_count = count - len(finite)
    if len(finite) == 0:
        return {"feature": name, "count": count, "null_count": null_count,
                "finite_count": 0, **{key: None for key in (
                    "min", "max", "mean", "stddev", "median", "mad", "p01", "p05",
                    "p25", "p50", "p75", "p95", "p99", "skewness")},
                "unique_count": 0, "non_informative": True, "mad_zero": True,
                "robust_01_clipped_low_count": 0, "robust_01_clipped_high_count": 0}
    median = statistics.median(finite)
    mad = statistics.median(abs(value - median) for value in finite)
    mean = statistics.fmean(finite)
    stddev = statistics.stdev(finite) if len(finite) > 1 else 0.0
    skewness = None
    if len(finite) > 2 and stddev > 0:
        population_stddev = statistics.pstdev(finite)
        skewness = statistics.fmean(((value - mean) / population_stddev) ** 3 for value in finite)
    p01 = linear_quantile(finite, 0.01)
    p99 = linear_quantile(finite, 0.99)
    return {
        "feature": name, "count": count, "null_count": null_count,
        "finite_count": len(finite), "min": min(finite), "max": max(finite),
        "mean": mean, "stddev": stddev, "median": median, "mad": mad,
        "p01": p01, "p05": linear_quantile(finite, 0.05),
        "p25": linear_quantile(finite, 0.25), "p50": median,
        "p75": linear_quantile(finite, 0.75), "p95": linear_quantile(finite, 0.95),
        "p99": p99, "skewness": skewness, "unique_count": len(set(finite)),
        "non_informative": p01 == p99, "mad_zero": mad == 0,
        "robust_01_clipped_low_count": sum(value < p01 for value in finite),
        "robust_01_clipped_high_count": sum(value > p99 for value in finite),
    }


def _pearson(left: list[float], right: list[float]) -> float | None:
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    left_delta = [value - left_mean for value in left]
    right_delta = [value - right_mean for value in right]
    denominator = math.sqrt(
        math.fsum(value * value for value in left_delta)
        * math.fsum(value * value for value in right_delta)
    )
    if denominator == 0:
        return None
    return math.fsum(x * y for x, y in zip(left_delta, right_delta)) / denominator


def correlations(columns: dict[str, list[float | None]]) -> list[dict[str, Any]]:
    output = []
    names = list(columns)
    for left_index, left in enumerate(names):
        for right in names[left_index + 1:]:
            pairs = [(x, y) for x, y in zip(columns[left], columns[right])
                     if x is not None and y is not None
                     and math.isfinite(float(x)) and math.isfinite(float(y))]
            if len(pairs) < 3:
                continue
            x = [float(pair[0]) for pair in pairs]
            y = [float(pair[1]) for pair in pairs]
            pearson = _pearson(x, y)
            rx = [float(value) for value in midrank_percentiles(x)]
            ry = [float(value) for value in midrank_percentiles(y)]
            spearman = _pearson(rx, ry)
            output.append({"left": left, "right": right, "sample_count": len(pairs),
                           "pearson": pearson, "spearman": spearman})
    return output


def build_profile(feature_hash: str, generated_at: str, row_count: int,
                  feature_schema_version: str, extractor_version: str,
                  profiles: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "normalization_profile": PROFILE_NAME,
        "normalization_version": NORMALIZATION_VERSION,
        "corpus_version": PROFILE_NAME,
        "corpus_row_count": row_count,
        "feature_schema_version": feature_schema_version,
        "feature_extractor_version": extractor_version,
        "source_feature_parquet_sha256": feature_hash,
        "generated_at_utc": generated_at,
        "rules": {
            "quantiles": "NumPy linear interpolation over finite non-null corpus values",
            "robust_01": "natural [0,1] values retained; otherwise clamp((x-P01)/(P99-P01),0,1)",
            "percentile_01": "empirical midrank with ties averaged, rank/(n-1); singleton=0.5",
            "robust_z": "(x-median)/(1.4826*MAD), null when MAD=0",
            "missing": "null input remains null; no imputation",
            "aspect": "ln(width/height) for positive dimensions",
            "hue": "circular cosine/sine diagnostics; excluded from color_core when a/b present",
            "color_axes": "raw OKLab L/a/b retained in color_core; normalized variants are not perceptual geometry",
        },
        "natural_01_features": sorted(NATURAL_01),
        "primary_vector_exclusions": PRIMARY_EXCLUSIONS,
        "feature_families": {name: list(fields) for name, fields in FAMILIES.items()},
        "features": profiles,
    }


def _metadata(profile: dict[str, Any]) -> dict[bytes, bytes]:
    compact = json.dumps(profile, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        b"smk.normalization_profile": PROFILE_NAME.encode(),
        b"smk.normalization_version": NORMALIZATION_VERSION.encode(),
        b"smk.profile_json": compact.encode(),
        b"smk.source_feature_parquet_sha256": profile["source_feature_parquet_sha256"].encode(),
    }


def _write_parquet(path: Path, rows: list[dict[str, Any]], metadata: dict[bytes, bytes],
                   schema: pa.Schema | None = None) -> None:
    table = pa.Table.from_pylist(rows, schema=schema)
    table = table.replace_schema_metadata(metadata)
    pq.write_table(table, path, compression="zstd", version="2.6", write_statistics=True)


def run(root: Path) -> dict[str, Any]:
    feature_path = root / "data" / "processed" / "artwork-visual-features-v1.parquet"
    profile_path = root / "data" / "processed" / "normalization-profile-v1.json"
    normalized_path = root / "data" / "processed" / "artwork-normalized-features-v1.parquet"
    vectors_path = root / "data" / "processed" / "artwork-feature-vectors-v1.parquet"
    statistics_path = root / "data" / "reports" / "normalization-statistics.parquet"
    summary_path = root / "data" / "reports" / "normalization-summary.json"

    parquet = pq.ParquetFile(feature_path)
    source_metadata = parquet.schema_arrow.metadata or {}
    rows = parquet.read().to_pylist()
    generated_at = source_metadata[b"smk.generated_at_utc"].decode()
    feature_schema_version = source_metadata[b"smk.feature_schema_version"].decode()
    extractor_version = source_metadata[b"smk.extractor_version"].decode()

    columns: dict[str, list[float | None]] = {name: [] for name in PROFILE_FEATURES}
    for row in rows:
        row["log_net_aspect_ratio"] = log_aspect_ratio(row["net_width_cm"], row["net_height_cm"])
        row["log_image_aspect_ratio"] = log_aspect_ratio(row["image_width_px"], row["image_height_px"])
        row["centroid_hue_x"], row["centroid_hue_y"] = hue_xy(row["centroid_hue_deg"])
        for name in PROFILE_FEATURES:
            columns[name].append(row[name])

    profiles = [feature_profile(name, columns[name]) for name in PROFILE_FEATURES]
    profile_by_name = {item["feature"]: item for item in profiles}
    profile = build_profile(sha256_file(feature_path), generated_at, len(rows),
                            feature_schema_version, extractor_version, profiles)
    profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    metadata = _metadata(profile)

    percentile_columns = {name: midrank_percentiles(values) for name, values in columns.items()}
    normalized_rows = []
    vector_rows = []
    family_coverage = {name: 0 for name in FAMILIES}
    all_family_count = 0
    for index, source in enumerate(rows):
        normalized: dict[str, Any] = {
            "smk_entity_id": source["smk_entity_id"], "object_number": source["object_number"],
            "normalization_profile": PROFILE_NAME, "normalization_version": NORMALIZATION_VERSION,
            "quality_flags": source["quality_flags"],
            "centroid_hue_deg": source["centroid_hue_deg"],
            "centroid_hue_x": source["centroid_hue_x"], "centroid_hue_y": source["centroid_hue_y"],
        }
        for name in PROFILE_FEATURES:
            item = profile_by_name[name]
            value = source[name]
            normalized[name] = value
            normalized[f"{name}_robust_01"] = robust_01(
                value, item["p01"], item["p99"], natural=name in NATURAL_01)
            normalized[f"{name}_percentile_01"] = percentile_columns[name][index]
            normalized[f"{name}_robust_z"] = robust_z(value, item["median"], item["mad"])
        normalized_rows.append(normalized)
        family_values = {name: [normalized[field] for field in fields]
                         for name, fields in FAMILIES.items()}
        complete = {name: all(value is not None for value in values)
                    for name, values in family_values.items()}
        for name, is_complete in complete.items():
            family_coverage[name] += int(is_complete)
        all_family_count += int(all(complete.values()))
        vector_rows.append({
            "smk_entity_id": source["smk_entity_id"], "object_number": source["object_number"],
            "normalization_profile": PROFILE_NAME, "normalization_version": NORMALIZATION_VERSION,
            "color_core": family_values["color_core_v1"],
            "visual_character": family_values["visual_character_v1"],
            "geometry": family_values["geometry_v1"],
            "color_core_complete": complete["color_core_v1"],
            "visual_character_complete": complete["visual_character_v1"],
            "geometry_complete": complete["geometry_v1"],
        })

    normalized_fields = [
        ("smk_entity_id", pa.string()), ("object_number", pa.string()),
        ("normalization_profile", pa.string()), ("normalization_version", pa.string()),
        ("quality_flags", pa.list_(pa.string())), ("centroid_hue_deg", pa.float64()),
        ("centroid_hue_x", pa.float64()), ("centroid_hue_y", pa.float64()),
    ]
    for name in PROFILE_FEATURES:
        normalized_fields.extend((
            (name, pa.float64()), (f"{name}_robust_01", pa.float64()),
            (f"{name}_percentile_01", pa.float64()), (f"{name}_robust_z", pa.float64()),
        ))
    vector_schema = pa.schema([
        ("smk_entity_id", pa.string()), ("object_number", pa.string()),
        ("normalization_profile", pa.string()), ("normalization_version", pa.string()),
        ("color_core", pa.list_(pa.float64(), len(FAMILIES["color_core_v1"]))),
        ("visual_character", pa.list_(pa.float64(), len(FAMILIES["visual_character_v1"]))),
        ("geometry", pa.list_(pa.float64(), len(FAMILIES["geometry_v1"]))),
        ("color_core_complete", pa.bool_()), ("visual_character_complete", pa.bool_()),
        ("geometry_complete", pa.bool_()),
    ])
    _write_parquet(normalized_path, normalized_rows, metadata, pa.schema(normalized_fields))
    _write_parquet(vectors_path, vector_rows, metadata, vector_schema)
    _write_parquet(statistics_path, profiles, metadata)

    corr_names = (
        "smk_brightness", "centroid_l", "smk_saturation", "centroid_chroma",
        "smk_contrast", "palette_spread_oklab", "smk_entropy", "lightness_stddev",
        "chroma_stddev",
    )
    correlation_rows = correlations({name: columns[name] for name in corr_names})
    redundant = [item for item in correlation_rows if
                 (item["pearson"] is not None and abs(item["pearson"]) >= 0.9)
                 or (item["spearman"] is not None and abs(item["spearman"]) >= 0.9)]
    examples = {}
    for object_number in ("KMS8892", "KMS1571", "KAS782", "KKS5261"):
        match = next((row for row in normalized_rows if row["object_number"] == object_number), None)
        if match:
            examples[object_number] = {name: match.get(name) for name in (
                "centroid_l", "centroid_l_robust_01", "centroid_l_percentile_01", "centroid_l_robust_z",
                "centroid_a", "centroid_b", "palette_spread_oklab",
                "palette_spread_oklab_robust_01", "palette_spread_oklab_percentile_01",
                "palette_spread_oklab_robust_z", "hue_concentration_01",
                "smk_brightness", "smk_contrast", "smk_saturation", "smk_entropy",
                "net_width_cm", "net_height_cm", "net_area_cm2", "log_net_aspect_ratio")}
    summary = {
        "normalization_profile": PROFILE_NAME, "normalization_version": NORMALIZATION_VERSION,
        "source_feature_parquet_sha256": profile["source_feature_parquet_sha256"],
        "row_count": len(rows), "feature_statistics": profiles,
        "high_null_features": [p["feature"] for p in profiles if p["null_count"] / p["count"] >= 0.5],
        "near_zero_variance_features": [p["feature"] for p in profiles if p["stddev"] is not None and p["stddev"] <= 1e-12],
        "extreme_skew_features": [p["feature"] for p in profiles if p["skewness"] is not None and abs(p["skewness"]) >= 2],
        "correlations": correlation_rows, "redundant_pairs_abs_correlation_gte_0_9": redundant,
        "family_coverage": {**family_coverage, "all_three": all_family_count},
        "examples": examples,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(run(args.root.resolve()), indent=2))


if __name__ == "__main__":
    main()

"""Build deterministic per-artwork visual features for smk-public-visual-v1."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from smk_playground.features.color import ACHROMATIC_EPSILON, COLOR_IMPLEMENTATION
from smk_playground.features.extract import ASPECT_MISMATCH_THRESHOLD, extract_artwork

FEATURE_SCHEMA_NAME = "artart-visual-features"
FEATURE_SCHEMA_VERSION = "1.0.0"
EXTRACTOR_VERSION = "1.0.0"
CORPUS_VERSION = "smk-public-visual-v1"

PROVENANCE_FIELDS = [
    ("feature_schema", pa.string()),
    ("feature_schema_version", pa.string()),
    ("extractor_version", pa.string()),
    ("generated_at_utc", pa.string()),
    ("canonical_dataset_sha256", pa.string()),
    ("corpus_definition", pa.string()),
    ("corpus_dataset_sha256", pa.string()),
    ("color_implementation", pa.string()),
]

FEATURE_SCHEMA = pa.schema([
    *PROVENANCE_FIELDS,
    ("smk_entity_id", pa.string()),
    ("object_number", pa.string()),
    ("palette_source", pa.string()),
    ("palette_weighting", pa.string()),
    ("palette_source_size", pa.int64()),
    ("palette_analytic_size", pa.int64()),
    ("source_palette", pa.list_(pa.string())),
    ("first_palette_color_hex", pa.string()),
    ("palette_source_order_preserved", pa.bool_()),
    ("centroid_l", pa.float64()),
    ("centroid_a", pa.float64()),
    ("centroid_b", pa.float64()),
    ("centroid_chroma", pa.float64()),
    ("centroid_hue_deg", pa.float64()),
    ("palette_entropy_01", pa.float64()),
    ("effective_palette_size", pa.float64()),
    ("palette_spread_oklab", pa.float64()),
    ("lightness_stddev", pa.float64()),
    ("chroma_stddev", pa.float64()),
    ("hue_concentration_01", pa.float64()),
    ("smk_brightness", pa.float64()),
    ("smk_contrast", pa.float64()),
    ("smk_saturation", pa.float64()),
    ("smk_entropy", pa.float64()),
    ("smk_colortemp", pa.float64()),
    ("net_width_cm", pa.float64()),
    ("net_height_cm", pa.float64()),
    ("net_area_cm2", pa.float64()),
    ("net_aspect_ratio", pa.float64()),
    ("log_net_width_cm", pa.float64()),
    ("log_net_height_cm", pa.float64()),
    ("log_net_area_cm2", pa.float64()),
    ("image_width_px", pa.int64()),
    ("image_height_px", pa.int64()),
    ("image_aspect_ratio", pa.float64()),
    ("aspect_mismatch_log", pa.float64()),
    ("canonical_quality_flags", pa.list_(pa.string())),
    ("feature_quality_flags", pa.list_(pa.string())),
    ("quality_flags", pa.list_(pa.string())),
])

PALETTE_SCHEMA = pa.schema([
    *PROVENANCE_FIELDS,
    ("smk_entity_id", pa.string()),
    ("object_number", pa.string()),
    ("palette_source", pa.string()),
    ("palette_weighting", pa.string()),
    ("palette_rank", pa.int64()),
    ("source_rank", pa.int64()),
    ("source_hex", pa.string()),
    ("hex", pa.string()),
    ("weight", pa.float64()),
    ("srgb_r", pa.float64()),
    ("srgb_g", pa.float64()),
    ("srgb_b", pa.float64()),
    ("oklab_l", pa.float64()),
    ("oklab_a", pa.float64()),
    ("oklab_b", pa.float64()),
    ("oklch_l", pa.float64()),
    ("oklch_c", pa.float64()),
    ("oklch_h_deg", pa.float64()),
])

DIAGNOSTIC_FIELDS = (
    "centroid_l", "centroid_chroma", "palette_spread_oklab", "lightness_stddev",
    "chroma_stddev", "palette_entropy_01", "effective_palette_size",
    "hue_concentration_01", "smk_brightness", "smk_contrast", "smk_saturation",
    "smk_entropy", "smk_colortemp", "net_area_cm2", "net_aspect_ratio",
    "image_aspect_ratio", "aspect_mismatch_log",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def percentiles(values: list[float]) -> dict[str, float | int | None]:
    finite = sorted(value for value in values if value is not None and math.isfinite(value))
    if not finite:
        return {"count": 0, "min": None, "p01": None, "p05": None, "p25": None,
                "median": None, "p75": None, "p95": None, "p99": None, "max": None}

    def quantile(probability: float) -> float:
        position = (len(finite) - 1) * probability
        low = int(position)
        high = min(low + 1, len(finite) - 1)
        fraction = position - low
        return finite[low] * (1 - fraction) + finite[high] * fraction

    return {
        "count": len(finite), "min": finite[0], "p01": quantile(0.01),
        "p05": quantile(0.05), "p25": quantile(0.25), "median": statistics.median(finite),
        "p75": quantile(0.75), "p95": quantile(0.95), "p99": quantile(0.99),
        "max": finite[-1],
    }


def _provenance(root: Path, canonical_path: Path, corpus_path: Path) -> dict[str, str]:
    manifest = json.loads(
        (root / "data" / "processed" / "source-manifest.json").read_text(encoding="utf-8")
    )
    return {
        "feature_schema": FEATURE_SCHEMA_NAME,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "extractor_version": EXTRACTOR_VERSION,
        # A fixed manifest timestamp makes identical inputs byte-reproducible across repeated runs.
        "generated_at_utc": manifest["generated_at_utc"],
        "canonical_dataset_sha256": sha256_file(canonical_path),
        "corpus_definition": CORPUS_VERSION,
        "corpus_dataset_sha256": sha256_file(corpus_path),
        "color_implementation": COLOR_IMPLEMENTATION,
    }


def _metadata(provenance: dict[str, str]) -> dict[bytes, bytes]:
    return {f"smk.{key}".encode(): value.encode() for key, value in provenance.items()}


def _example_payload(
    feature: dict[str, Any], palette: list[dict[str, Any]], in_corpus: bool,
) -> dict[str, Any]:
    return {
        "in_corpus": in_corpus,
        "smk_entity_id": feature["smk_entity_id"],
        "object_number": feature["object_number"],
        "source_palette": feature["source_palette"],
        "analytical_palette": [
            {
                "rank": row["palette_rank"], "source_rank": row["source_rank"],
                "hex": row["hex"], "weight": row["weight"], "oklch_l": row["oklch_l"],
                "oklch_c": row["oklch_c"], "oklch_h_deg": row["oklch_h_deg"],
            }
            for row in palette
        ],
        "centroid": {
            key: feature[key] for key in
            ("centroid_l", "centroid_a", "centroid_b", "centroid_chroma", "centroid_hue_deg")
        },
        "palette_spread_oklab": feature["palette_spread_oklab"],
        "hue_concentration_01": feature["hue_concentration_01"],
        "source_visual": {
            key: feature[key] for key in
            ("smk_brightness", "smk_contrast", "smk_saturation", "smk_entropy", "smk_colortemp")
        },
        "geometry": {
            key: feature[key] for key in
            ("net_width_cm", "net_height_cm", "net_area_cm2", "net_aspect_ratio",
             "image_width_px", "image_height_px", "image_aspect_ratio", "aspect_mismatch_log")
        },
        "flags": feature["quality_flags"],
    }


def run(root: Path) -> dict[str, Any]:
    canonical_path = root / "data" / "processed" / "artworks.parquet"
    corpus_path = root / "data" / "processed" / "smk-public-visual-v1.parquet"
    features_path = root / "data" / "processed" / "artwork-visual-features-v1.parquet"
    palettes_path = root / "data" / "processed" / "artwork-palettes-v1.parquet"
    report_path = root / "data" / "reports" / "feature-summary.json"
    examples_path = root / "data" / "reports" / "feature-examples.json"
    provenance = _provenance(root, canonical_path, corpus_path)
    metadata = _metadata(provenance)
    feature_writer = pq.ParquetWriter(features_path, FEATURE_SCHEMA.with_metadata(metadata), compression="zstd")
    palette_writer = pq.ParquetWriter(palettes_path, PALETTE_SCHEMA.with_metadata(metadata), compression="zstd")
    diagnostics: dict[str, list[float]] = {field: [] for field in DIAGNOSTIC_FIELDS}
    palette_sizes: Counter[int] = Counter()
    flag_counts: Counter[str] = Counter()
    feature_flag_counts: Counter[str] = Counter()
    visual_nulls: Counter[str] = Counter()
    palette_rows_count = 0
    palette_achromatic_colors = 0
    centroid_null_hue_count = 0
    hue_concentration_null_count = 0
    examples: dict[str, dict[str, Any]] = {}
    selectors: dict[str, tuple[float, dict[str, Any], list[dict[str, Any]]] | None] = {
        "near_achromatic": None, "high_spread": None,
    }
    physical_example: tuple[dict[str, Any], list[dict[str, Any]]] | None = None
    missing_physical_example: tuple[dict[str, Any], list[dict[str, Any]]] | None = None
    feature_count = 0
    try:
        parquet = pq.ParquetFile(corpus_path)
        for batch in parquet.iter_batches(batch_size=1_000):
            feature_rows: list[dict[str, Any]] = []
            palette_rows: list[dict[str, Any]] = []
            for canonical in batch.to_pylist():
                feature, palette = extract_artwork(canonical)
                feature_count += 1
                palette_sizes[feature["palette_analytic_size"]] += 1
                for flag in feature["quality_flags"]:
                    flag_counts[flag] += 1
                for flag in feature["feature_quality_flags"]:
                    feature_flag_counts[flag] += 1
                if feature["centroid_hue_deg"] is None:
                    centroid_null_hue_count += 1
                if feature["hue_concentration_01"] is None:
                    hue_concentration_null_count += 1
                for field in DIAGNOSTIC_FIELDS:
                    value = feature[field]
                    if value is not None:
                        diagnostics[field].append(value)
                for field in ("smk_brightness", "smk_contrast", "smk_saturation", "smk_entropy", "smk_colortemp"):
                    if feature[field] is None:
                        visual_nulls[field] += 1
                if feature["object_number"] == "KMS8892":
                    examples["KMS8892"] = _example_payload(feature, palette, True)
                chroma = feature["centroid_chroma"]
                if chroma is not None and (
                    selectors["near_achromatic"] is None or chroma < selectors["near_achromatic"][0]
                ):
                    selectors["near_achromatic"] = (chroma, feature, palette)
                spread = feature["palette_spread_oklab"]
                if spread is not None and chroma is not None and chroma >= 0.07 and (
                    selectors["high_spread"] is None or spread > selectors["high_spread"][0]
                ):
                    selectors["high_spread"] = (spread, feature, palette)
                if physical_example is None and feature["net_area_cm2"] is not None:
                    physical_example = (feature, palette)
                if missing_physical_example is None and feature["net_area_cm2"] is None:
                    missing_physical_example = (feature, palette)
                feature_rows.append({**provenance, **feature})
                for palette_row in palette:
                    if palette_row["oklch_h_deg"] is None:
                        palette_achromatic_colors += 1
                    palette_rows.append({
                        **provenance,
                        "smk_entity_id": feature["smk_entity_id"],
                        "object_number": feature["object_number"],
                        "palette_source": feature["palette_source"],
                        "palette_weighting": feature["palette_weighting"],
                        **palette_row,
                    })
                if abs(math.fsum(row["weight"] for row in palette) - 1.0) > 1e-12:
                    raise ValueError(f"Palette weights do not sum to one: {feature['smk_entity_id']}")
            feature_writer.write_table(pa.Table.from_pylist(feature_rows, schema=FEATURE_SCHEMA))
            palette_writer.write_table(pa.Table.from_pylist(palette_rows, schema=PALETTE_SCHEMA))
            palette_rows_count += len(palette_rows)
    finally:
        feature_writer.close()
        palette_writer.close()

    for name, selected in selectors.items():
        if selected:
            examples[name] = _example_payload(selected[1], selected[2], True)
    if physical_example:
        examples["with_physical_dimensions"] = _example_payload(*physical_example, True)
    if missing_physical_example:
        examples["without_physical_dimensions"] = _example_payload(*missing_physical_example, True)

    kks_table = pq.read_table(canonical_path, filters=[("object_number", "=", "KKS8001")])
    if kks_table.num_rows == 1:
        kks_feature, kks_palette = extract_artwork(kks_table.to_pylist()[0])
        examples["KKS8001"] = _example_payload(kks_feature, kks_palette, False)

    summary = {
        **provenance,
        "achromatic_epsilon": ACHROMATIC_EPSILON,
        "aspect_mismatch_threshold_log": ASPECT_MISMATCH_THRESHOLD,
        "feature_rows": feature_count,
        "palette_rows": palette_rows_count,
        "palette_size_distribution": dict(sorted(palette_sizes.items())),
        "palette_achromatic_color_rows": palette_achromatic_colors,
        "centroid_null_hue_count": centroid_null_hue_count,
        "hue_concentration_null_count": hue_concentration_null_count,
        "feature_quality_flag_counts": dict(sorted(feature_flag_counts.items())),
        "all_quality_flag_counts": dict(sorted(flag_counts.items())),
        "source_visual_null_counts": dict(visual_nulls),
        "distributions": {field: percentiles(values) for field, values in diagnostics.items()},
    }
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    examples_path.write_text(json.dumps(examples, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(run(args.root.resolve()), indent=2))


if __name__ == "__main__":
    main()

"""Milestone 1 streaming ingest and source-audit artifact generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from .source import (
    HEX_COLOR_RE,
    iter_source_records,
    logical_json,
    logical_sha256,
    normalize_dimension_axis,
    normalize_dimension_unit,
    normalized_dimensions,
    parse_strict_number,
    source_row_id,
)

VISUAL_FIELDS = ("brightness", "contrast", "saturation", "entropy", "colortemp")
SOURCE_FIELDS = (
    "id", "object_number", "created", "modified", "public_domain", "rights", "has_image",
    "image_width", "image_height", "image_mime_type", "image_iiif_id", "image_iiif_info",
    "image_thumbnail", "image_native", "colors", "brightness", "contrast", "saturation",
    "entropy", "colortemp", "dimensions", "titles", "object_names", "classification",
    "classifications",
)
MANIFEST_HASH_FIELDS = {"manifest_version", "generated_at_utc", "reconnaissance_tool", "sources"}

SOURCE_SCHEMA = pa.schema([
    ("source_row_id", pa.string()),
    ("source_language", pa.string()),
    ("source_path", pa.string()),
    ("source_file_sha256", pa.string()),
    ("source_manifest_sha256", pa.string()),
    ("smk_source_id", pa.string()),
    ("object_number", pa.string()),
    ("created", pa.string()),
    ("modified", pa.string()),
    ("public_domain", pa.bool_()),
    ("rights", pa.string()),
    ("has_image", pa.bool_()),
    ("image_width", pa.int64()),
    ("image_height", pa.int64()),
    ("image_iiif_id", pa.string()),
    ("image_iiif_info", pa.string()),
    ("image_thumbnail", pa.string()),
    ("image_native", pa.string()),
    ("colors_json", pa.string()),
    ("dimensions_json", pa.string()),
    ("titles_json", pa.string()),
    ("object_names_json", pa.string()),
    ("visual_json", pa.string()),
    ("normalized_dimensions_json", pa.string()),
    ("record_logical_sha256", pa.string()),
    ("source_record_json", pa.string()),
])


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _optional_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _json_or_none(value: Any) -> str | None:
    return logical_json(value) if value is not None else None


def _manifest_sha256(manifest: dict[str, Any]) -> str:
    stable = {key: manifest[key] for key in sorted(MANIFEST_HASH_FIELDS) if key in manifest}
    return hashlib.sha256(logical_json(stable).encode()).hexdigest()


def _source_info(manifest: dict[str, Any], language: str) -> dict[str, Any]:
    return next(source for source in manifest["sources"] if source["language"] == language)


class AuditState:
    def __init__(self, language: str) -> None:
        self.language = language
        self.row_ids: set[str] = set()
        self.smk_ids: set[str] = set()
        self.object_counts: Counter[str] = Counter()
        self.dimension_vocab: Counter[tuple[str, str, str, str, str, str]] = Counter()
        self.dimension_values: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        self.dimension_issues: Counter[str] = Counter()
        self.dimension_duplicate_measurements = 0
        self.dimension_conflicting_measurements = 0
        self.palette_lengths: Counter[int] = Counter()
        self.palette_missing = 0
        self.palette_invalid = 0
        self.palette_duplicate_records = 0
        self.palette_invalid_examples: list[dict[str, str]] = []
        self.visual_values: dict[str, list[float]] = {field: [] for field in VISUAL_FIELDS}
        self.visual_types: dict[str, Counter[str]] = {field: Counter() for field in VISUAL_FIELDS}
        self.visual_malformed: dict[str, list[dict[str, Any]]] = {field: [] for field in VISUAL_FIELDS}
        self.rights: Counter[str] = Counter()
        self.public_domain: Counter[str] = Counter()
        self.has_image: Counter[str] = Counter()
        self.image_url_presence: Counter[str] = Counter()

    def observe(self, record: dict[str, Any], row_id: str) -> None:
        if row_id in self.row_ids:
            raise ValueError(f"Non-unique source_row_id: {row_id}")
        self.row_ids.add(row_id)
        smk_id = record.get("id")
        if isinstance(smk_id, str) and smk_id:
            if smk_id in self.smk_ids:
                raise ValueError(f"SMK id is not unique in {self.language}: {smk_id}")
            self.smk_ids.add(smk_id)
        object_number = record.get("object_number")
        if isinstance(object_number, str):
            self.object_counts[object_number] += 1

        self._observe_dimensions(record, row_id)
        self._observe_palette(record)
        self._observe_visuals(record)
        rights = record.get("rights")
        self.rights[str(rights) if rights is not None else "<missing>"] += 1
        self.public_domain[str(record.get("public_domain"))] += 1
        self.has_image[str(record.get("has_image"))] += 1
        has_public_url = any(record.get(key) for key in ("image_native", "image_thumbnail", "image_iiif_id"))
        self.image_url_presence[str(bool(has_public_url))] += 1

    def _observe_dimensions(self, record: dict[str, Any], row_id: str) -> None:
        dimensions = record.get("dimensions")
        if not isinstance(dimensions, list):
            self.dimension_issues["dimensions_not_array_or_missing"] += 1
            return
        seen: Counter[tuple[str, str, str, str]] = Counter()
        grouped: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        for item in dimensions:
            if not isinstance(item, dict):
                self.dimension_issues["dimension_item_not_object"] += 1
                continue
            part = str(item.get("part") or "")
            dim_type = str(item.get("type") or "")
            unit = str(item.get("unit") or "")
            raw_value = item.get("value")
            value_text = "" if raw_value is None else str(raw_value)
            _, number_status = parse_strict_number(raw_value)
            axis = normalize_dimension_axis(dim_type) or "<unmapped>"
            normalized_unit = normalize_dimension_unit(unit) or "<unmapped>"
            self.dimension_vocab[(part, dim_type, unit, axis, normalized_unit, number_status)] += 1
            self.dimension_values[(part, dim_type, unit)].add(value_text)
            if not part: self.dimension_issues["missing_part"] += 1
            if not dim_type: self.dimension_issues["missing_type"] += 1
            if not unit: self.dimension_issues["missing_unit"] += 1
            if number_status not in {"numeric", "numeric_text"}:
                self.dimension_issues[f"value_{number_status}"] += 1
            key = (part, dim_type, unit, value_text)
            seen[key] += 1
            grouped[(part, dim_type, unit)].add(value_text)
        self.dimension_duplicate_measurements += sum(count - 1 for count in seen.values() if count > 1)
        self.dimension_conflicting_measurements += sum(1 for values in grouped.values() if len(values) > 1)

    def _observe_palette(self, record: dict[str, Any]) -> None:
        colors = record.get("colors")
        if not isinstance(colors, list):
            self.palette_missing += 1
            return
        self.palette_lengths[len(colors)] += 1
        normalized: list[str] = []
        for color in colors:
            if isinstance(color, str) and HEX_COLOR_RE.fullmatch(color):
                normalized.append(color.casefold())
            else:
                self.palette_invalid += 1
                if len(self.palette_invalid_examples) < 20:
                    self.palette_invalid_examples.append({
                        "object_number": str(record.get("object_number")), "value": repr(color),
                    })
        if len(set(normalized)) < len(normalized):
            self.palette_duplicate_records += 1

    def _observe_visuals(self, record: dict[str, Any]) -> None:
        for field in VISUAL_FIELDS:
            raw = record.get(field)
            type_name = type(raw).__name__ if raw is not None else "missing"
            self.visual_types[field][type_name] += 1
            number, status = parse_strict_number(raw)
            if number is not None:
                self.visual_values[field].append(number)
            elif raw is not None and len(self.visual_malformed[field]) < 30:
                self.visual_malformed[field].append({
                    "object_number": record.get("object_number"), "value": raw, "status": status,
                })


def _source_row(
    record: dict[str, Any], language: str, source: dict[str, Any], manifest_sha: str,
) -> dict[str, Any]:
    visual = {field: record.get(field) for field in VISUAL_FIELDS if field in record}
    return {
        "source_row_id": source_row_id(language, record),
        "source_language": language,
        "source_path": source["path"],
        "source_file_sha256": source["sha256"],
        "source_manifest_sha256": manifest_sha,
        "smk_source_id": _optional_string(record.get("id")),
        "object_number": _optional_string(record.get("object_number")),
        "created": _optional_string(record.get("created")),
        "modified": _optional_string(record.get("modified")),
        "public_domain": _optional_bool(record.get("public_domain")),
        "rights": _optional_string(record.get("rights")),
        "has_image": _optional_bool(record.get("has_image")),
        "image_width": _optional_int(record.get("image_width")),
        "image_height": _optional_int(record.get("image_height")),
        "image_iiif_id": _optional_string(record.get("image_iiif_id")),
        "image_iiif_info": _optional_string(record.get("image_iiif_info")),
        "image_thumbnail": _optional_string(record.get("image_thumbnail")),
        "image_native": _optional_string(record.get("image_native")),
        "colors_json": _json_or_none(record.get("colors")),
        "dimensions_json": _json_or_none(record.get("dimensions")),
        "titles_json": _json_or_none(record.get("titles")),
        "object_names_json": _json_or_none(record.get("object_names")),
        "visual_json": logical_json(visual),
        "normalized_dimensions_json": logical_json(normalized_dimensions(record)),
        "record_logical_sha256": logical_sha256(record),
        "source_record_json": logical_json(record),
    }


def ingest_source(
    root: Path, language: str, manifest: dict[str, Any], batch_size: int = 1_000,
) -> AuditState:
    source = _source_info(manifest, language)
    source_path = root / source["path"]
    output_path = root / "data" / "interim" / f"source_{language}.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_sha = _manifest_sha256(manifest)
    metadata = {
        b"smk.source_manifest_sha256": manifest_sha.encode(),
        b"smk.source_file_sha256": source["sha256"].encode(),
        b"smk.source_language": language.encode(),
        b"smk.logical_lossless": b"source_record_json preserves the complete parsed JSON record",
    }
    writer = pq.ParquetWriter(output_path, SOURCE_SCHEMA.with_metadata(metadata), compression="zstd")
    state = AuditState(language)
    batch: list[dict[str, Any]] = []
    try:
        for record in iter_source_records(source_path):
            row = _source_row(record, language, source, manifest_sha)
            state.observe(record, row["source_row_id"])
            batch.append(row)
            if len(batch) >= batch_size:
                writer.write_table(pa.Table.from_pylist(batch, schema=SOURCE_SCHEMA))
                batch.clear()
        if batch:
            writer.write_table(pa.Table.from_pylist(batch, schema=SOURCE_SCHEMA))
    finally:
        writer.close()
    if len(state.row_ids) != source["record_count"]:
        raise ValueError(f"{language} row count differs from source manifest")
    return state


def _read_rows(path: Path, columns: list[str] | None = None) -> list[dict[str, Any]]:
    return pq.read_table(path, columns=columns).to_pylist()


def write_duplicate_report(root: Path, states: dict[str, AuditState]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    taxonomy = Counter()
    for language, state in states.items():
        duplicate_ids = {key for key, count in state.object_counts.items() if count > 1}
        source_rows = _read_rows(root / "data" / "interim" / f"source_{language}.parquet")
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in source_rows:
            if row["object_number"] in duplicate_ids:
                groups[row["object_number"]].append(row)
        for object_number, group in sorted(groups.items()):
            hashes = {row["record_logical_sha256"] for row in group}
            records = [json.loads(row["source_record_json"]) for row in group]
            differing = [
                field for field in sorted(set().union(*(record.keys() for record in records)))
                if len({logical_json(record.get(field)) for record in records}) > 1
            ]
            if len(hashes) == 1:
                category = "exact_logical_duplicate"
            elif all(record.get("id") == records[0].get("id") for record in records):
                category = "same_source_id_changed_record"
            elif any("verso" in str(record.get("object_number", "")).casefold() for record in records):
                category = "possible_alternate_or_subrecord"
            elif all(record.get("id") for record in records):
                category = "multiple_source_records_same_object_number"
            else:
                category = "unresolved"
            taxonomy[category] += 1
            for row, record in zip(group, records, strict=True):
                rows.append({
                    "language": language,
                    "object_number": object_number,
                    "occurrence_count": len(group),
                    "source_row_id": row["source_row_id"],
                    "smk_source_id": row["smk_source_id"],
                    "record_logical_sha256": row["record_logical_sha256"],
                    "logically_identical_group": len(hashes) == 1,
                    "byte_identical": False if len(hashes) > 1 else None,
                    "byte_identity_note": (
                        "Logical content differs, therefore source bytes cannot be identical"
                        if len(hashes) > 1 else
                        "Logical content matches; source byte spans were not retained"
                    ),
                    "differing_fields_json": logical_json(differing),
                    "classification": category,
                    "modified": row["modified"],
                    "image_identifiers_json": logical_json({
                        key: record.get(key) for key in
                        ("image_iiif_id", "image_iiif_info", "image_native", "image_thumbnail")
                    }),
                    "titles_json": row["titles_json"],
                    "object_type_json": logical_json({
                        "object_names": record.get("object_names"),
                        "classification": record.get("classification"),
                        "classifications": record.get("classifications"),
                    }),
                    "rights": row["rights"],
                    "dimensions_json": row["dimensions_json"],
                    "colors_json": row["colors_json"],
                    "visual_json": row["visual_json"],
                })
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, root / "data" / "reports" / "duplicate-object-numbers.parquet", compression="zstd")
    return {"groups_by_taxonomy": dict(taxonomy), "rows": len(rows)}


def write_dimension_report(root: Path, states: dict[str, AuditState]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}
    for language, state in states.items():
        for (part, dim_type, unit, axis, normalized_unit, value_status), count in sorted(state.dimension_vocab.items()):
            values = state.dimension_values[(part, dim_type, unit)]
            rows.append({
                "language": language, "part": part, "type": dim_type, "unit": unit,
                "proposed_axis": axis, "proposed_unit": normalized_unit,
                "value_status": value_status, "count": count, "distinct_value_count": len(values),
            })
        summary[language] = {
            "issues": dict(state.dimension_issues),
            "duplicate_measurements_beyond_first": state.dimension_duplicate_measurements,
            "conflicting_part_type_unit_groups": state.dimension_conflicting_measurements,
            "vocabulary_rows": sum(1 for row in rows if row["language"] == language),
        }
    pq.write_table(pa.Table.from_pylist(rows), root / "data" / "reports" / "dimension-vocabulary.parquet", compression="zstd")
    return summary


def _comparison_value(row: dict[str, Any], field: str) -> Any:
    if field == "colors": return json.loads(row["colors_json"]) if row["colors_json"] else None
    if field == "dimensions": return json.loads(row["normalized_dimensions_json"])
    if field in VISUAL_FIELDS:
        return json.loads(row["visual_json"]).get(field)
    return row.get(field)


def write_disagreement_report(root: Path, states: dict[str, AuditState]) -> dict[str, Any]:
    columns = [
        "source_row_id", "object_number", "rights", "public_domain", "has_image", "image_width",
        "image_height", "image_iiif_id", "image_iiif_info", "image_thumbnail", "image_native",
        "colors_json", "visual_json", "normalized_dimensions_json",
    ]
    by_language: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for language in ("da", "en"):
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in _read_rows(root / "data" / "interim" / f"source_{language}.parquet", columns):
            grouped[row["object_number"]].append(row)
        by_language[language] = grouped
    fields = (
        "rights", "public_domain", "has_image", "image_width", "image_height", "image_iiif_id",
        "image_iiif_info", "image_thumbnail", "image_native", "colors", *VISUAL_FIELDS, "dimensions",
    )
    rows: list[dict[str, Any]] = []
    classifications = Counter()
    overlap = sorted(set(by_language["da"]) & set(by_language["en"]))
    for object_number in overlap:
        da_group = by_language["da"][object_number]
        en_group = by_language["en"][object_number]
        if len(da_group) != 1 or len(en_group) != 1:
            classifications["duplicate_identity_requires_resolution"] += 1
            rows.append({
                "object_number": object_number, "field": "<identity>",
                "classification": "duplicate_identity_requires_resolution",
                "da_value_json": logical_json([row["source_row_id"] for row in da_group]),
                "en_value_json": logical_json([row["source_row_id"] for row in en_group]),
                "da_source_row_id": None, "en_source_row_id": None,
            })
            continue
        da_row, en_row = da_group[0], en_group[0]
        for field in fields:
            da_value = _comparison_value(da_row, field)
            en_value = _comparison_value(en_row, field)
            if logical_json(da_value) == logical_json(en_value):
                continue
            if da_value is None and en_value is not None:
                category = "missing_in_da"
            elif en_value is None and da_value is not None:
                category = "missing_in_en"
            elif field == "rights":
                category = "localized_or_license_text_difference"
            elif field == "dimensions":
                category = "normalized_dimension_difference"
            elif field.startswith("image_") or field == "has_image":
                category = "image_metadata_difference"
            else:
                category = "value_difference"
            classifications[f"{field}:{category}"] += 1
            rows.append({
                "object_number": object_number, "field": field, "classification": category,
                "da_value_json": logical_json(da_value), "en_value_json": logical_json(en_value),
                "da_source_row_id": da_row["source_row_id"],
                "en_source_row_id": en_row["source_row_id"],
            })
    pq.write_table(pa.Table.from_pylist(rows), root / "data" / "reports" / "source-disagreements.parquet", compression="zstd")
    return {"overlap": len(overlap), "disagreement_rows": len(rows), "classifications": dict(classifications)}


def _percentiles(values: list[float]) -> dict[str, float] | None:
    if not values: return None
    ordered = sorted(values)
    def quantile(p: float) -> float:
        position = (len(ordered) - 1) * p
        low = int(position)
        high = min(low + 1, len(ordered) - 1)
        fraction = position - low
        return ordered[low] * (1 - fraction) + ordered[high] * fraction
    return {
        "min": ordered[0], "p01": quantile(0.01), "p05": quantile(0.05),
        "p25": quantile(0.25), "median": statistics.median(ordered), "p75": quantile(0.75),
        "p95": quantile(0.95), "p99": quantile(0.99), "max": ordered[-1],
    }


def write_profiles(root: Path, states: dict[str, AuditState], disagreements: dict[str, Any]) -> None:
    palette_visual: dict[str, Any] = {"languages": {}}
    rights: dict[str, Any] = {"languages": {}}
    for language, state in states.items():
        visual = {}
        for field in VISUAL_FIELDS:
            visual[field] = {
                "datatype_counts": dict(state.visual_types[field]),
                "valid_numeric_count": len(state.visual_values[field]),
                "statistics": _percentiles(state.visual_values[field]),
                "malformed_examples": state.visual_malformed[field],
            }
        palette_visual["languages"][language] = {
            "colors_missing_or_non_array": state.palette_missing,
            "palette_length_distribution": dict(sorted(state.palette_lengths.items())),
            "invalid_color_values": state.palette_invalid,
            "invalid_color_examples": state.palette_invalid_examples,
            "records_with_duplicate_colors": state.palette_duplicate_records,
            "visual_fields": visual,
        }
        rights["languages"][language] = {
            "rights_value_counts": dict(state.rights.most_common()),
            "public_domain_counts": dict(state.public_domain),
            "has_image_counts": dict(state.has_image),
            "public_image_url_presence": dict(state.image_url_presence),
        }
    palette_visual["disagreement_classifications"] = disagreements["classifications"]
    report_dir = root / "data" / "reports"
    (report_dir / "palette-visual-profile.json").write_text(
        json.dumps(palette_visual, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    (report_dir / "rights-public-domain-profile.json").write_text(
        json.dumps(rights, ensure_ascii=False, indent=2), encoding="utf-8",
    )


def run(root: Path) -> dict[str, Any]:
    manifest_path = root / "data" / "processed" / "source-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    states = {language: ingest_source(root, language, manifest) for language in ("da", "en")}
    duplicate_summary = write_duplicate_report(root, states)
    dimension_summary = write_dimension_report(root, states)
    disagreement_summary = write_disagreement_report(root, states)
    write_profiles(root, states, disagreement_summary)
    summary = {
        "source_manifest_sha256": _manifest_sha256(manifest),
        "source_rows": {language: len(state.row_ids) for language, state in states.items()},
        "unique_smk_source_ids": {language: len(state.smk_ids) for language, state in states.items()},
        "duplicates": duplicate_summary,
        "dimensions": dimension_summary,
        "disagreements": disagreement_summary,
    }
    (root / "data" / "reports" / "milestone1-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(run(args.root.resolve()), indent=2))


if __name__ == "__main__":
    main()

"""Build the Milestone 2 canonical entity layer and frozen visual corpus."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from smk_playground.canonical.rules import (
    IMAGE_KEYS,
    SUPPORTED_AXES,
    SUPPORTED_PARTS,
    corpus_membership,
    dimension_slots,
    image_bundle,
    image_bundle_complete,
    is_extreme_colortemp,
    normalize_dimension_observations,
    resolve_image_bundle,
    resolve_scalar,
    resolve_smk_entity_id,
    rights_semantic,
    robust_colortemp_parameters,
    visual_number,
)
from smk_playground.ingest.source import logical_json

CANONICAL_VERSION = "1.0.0"
VISUAL_FIELDS = ("brightness", "contrast", "saturation", "entropy", "colortemp")
DIMENSION_STRUCT = pa.struct([
    ("part_canonical", pa.string()),
    ("type_canonical", pa.string()),
    ("unit_canonical", pa.string()),
    ("value_canonical", pa.float64()),
    ("original_language", pa.string()),
    ("original_part", pa.string()),
    ("original_type", pa.string()),
    ("original_unit", pa.string()),
    ("original_value", pa.string()),
    ("source_row_id", pa.string()),
    ("status", pa.string()),
])


def _schema() -> pa.Schema:
    fields: list[tuple[str, pa.DataType]] = [
        ("canonical_schema_version", pa.string()),
        ("smk_entity_id", pa.string()),
        ("object_number", pa.string()),
        ("object_number_da", pa.string()),
        ("object_number_en", pa.string()),
        ("object_number_provenance", pa.string()),
        ("object_number_status", pa.string()),
        ("source_row_id_da", pa.string()),
        ("source_row_id_en", pa.string()),
        ("present_in_da", pa.bool_()),
        ("present_in_en", pa.bool_()),
        ("source_manifest_sha256_da", pa.string()),
        ("source_manifest_sha256_en", pa.string()),
        ("source_file_sha256_da", pa.string()),
        ("source_file_sha256_en", pa.string()),
        ("titles_da_json", pa.string()),
        ("titles_en_json", pa.string()),
        ("object_names_da_json", pa.string()),
        ("object_names_en_json", pa.string()),
        ("classifications_da_json", pa.string()),
        ("classifications_en_json", pa.string()),
        ("artists_da_json", pa.string()),
        ("artists_en_json", pa.string()),
        ("production_da_json", pa.string()),
        ("production_en_json", pa.string()),
        ("production_dates_da_json", pa.string()),
        ("production_dates_en_json", pa.string()),
        ("techniques_da_json", pa.string()),
        ("techniques_en_json", pa.string()),
        ("materials_da_json", pa.string()),
        ("materials_en_json", pa.string()),
        ("public_domain", pa.bool_()),
        ("public_domain_da", pa.bool_()),
        ("public_domain_en", pa.bool_()),
        ("public_domain_provenance", pa.string()),
        ("public_domain_status", pa.string()),
        ("rights_da", pa.string()),
        ("rights_en", pa.string()),
        ("rights_semantic", pa.string()),
        ("rights_semantic_da", pa.string()),
        ("rights_semantic_en", pa.string()),
        ("rights_provenance", pa.string()),
        ("rights_status", pa.string()),
        ("colors", pa.list_(pa.string())),
        ("colors_da", pa.list_(pa.string())),
        ("colors_en", pa.list_(pa.string())),
        ("colors_provenance", pa.string()),
        ("colors_status", pa.string()),
    ]
    for field in VISUAL_FIELDS:
        fields.extend([
            (field, pa.float64()),
            (f"{field}_da_json", pa.string()),
            (f"{field}_en_json", pa.string()),
            (f"{field}_provenance", pa.string()),
            (f"{field}_status", pa.string()),
        ])
    fields.extend([
        ("image_bundle_status", pa.string()),
        ("image_bundle_provenance", pa.string()),
        ("image_bundle_complete", pa.bool_()),
        ("image_bundle_da_json", pa.string()),
        ("image_bundle_en_json", pa.string()),
        ("has_image", pa.bool_()),
        ("image_iiif_id", pa.string()),
        ("image_iiif_info", pa.string()),
        ("image_width", pa.int64()),
        ("image_height", pa.int64()),
        ("image_thumbnail", pa.string()),
        ("image_native", pa.string()),
        ("image_mime_type", pa.string()),
        ("image_cropped", pa.bool_()),
        ("image_orientation", pa.string()),
        ("image_hq", pa.bool_()),
        ("dimension_observations", pa.list_(DIMENSION_STRUCT)),
        ("dimension_conflict_slots", pa.list_(pa.string())),
        ("dimension_conflict_candidates", pa.list_(DIMENSION_STRUCT)),
    ])
    for part in SUPPORTED_PARTS:
        for axis in SUPPORTED_AXES:
            fields.append((f"{part}_{axis}_cm", pa.float64()))
    fields.extend([
        ("has_net_width", pa.bool_()),
        ("has_net_height", pa.bool_()),
        ("has_2d_physical_geometry", pa.bool_()),
        ("has_3d_physical_geometry", pa.bool_()),
        ("has_any_physical_dimension", pa.bool_()),
        ("quality_flags", pa.list_(pa.string())),
        ("previous_public_visual_candidate", pa.bool_()),
        ("corpus_smk_public_visual_v1", pa.bool_()),
        ("corpus_exclusion_reasons", pa.list_(pa.string())),
    ])
    return pa.schema(fields)


MEMBERSHIP_SCHEMA = pa.schema([
    ("smk_entity_id", pa.string()),
    ("object_number", pa.string()),
    ("included", pa.bool_()),
    ("exclusion_reasons", pa.list_(pa.string())),
    ("quality_flags", pa.list_(pa.string())),
])

GROUP_SCHEMA = pa.schema([
    ("object_number", pa.string()),
    ("canonical_entity_ids", pa.list_(pa.string())),
    ("group_size", pa.int64()),
    ("group_classification", pa.string()),
    ("ambiguity_flag", pa.bool_()),
    ("corpus_member_count", pa.int64()),
])


def _raw_value(record: dict[str, Any] | None, key: str) -> Any:
    return record.get(key) if record else None


def _json_value(record: dict[str, Any] | None, key: str) -> str | None:
    value = _raw_value(record, key)
    return logical_json(value) if value is not None else None


def _localized_fields(row: dict[str, Any], da: dict[str, Any] | None, en: dict[str, Any] | None) -> None:
    mappings = {
        "titles": "titles",
        "object_names": "object_names",
        "classifications": "classification",
        "artists": "artist",
        "production": "production",
        "production_dates": "production_date",
        "techniques": "techniques",
        "materials": "materials",
    }
    for output, source in mappings.items():
        row[f"{output}_da_json"] = _json_value(da, source)
        row[f"{output}_en_json"] = _json_value(en, source)


def _visual_fields(
    row: dict[str, Any], da: dict[str, Any] | None, en: dict[str, Any] | None,
) -> list[str]:
    flags: list[str] = []
    for field in VISUAL_FIELDS:
        da_raw = _raw_value(da, field)
        en_raw = _raw_value(en, field)
        da_number, da_status = visual_number(da, field)
        en_number, en_status = visual_number(en, field)
        canonical, provenance, status = resolve_scalar(da_number, en_number)
        if da_raw is not None and da_number is None:
            status = f"invalid_da:{da_status}"
        if en_raw is not None and en_number is None:
            status = f"invalid_en:{en_status}" if status == "missing" else f"{status}|invalid_en:{en_status}"
        row[field] = canonical
        row[f"{field}_da_json"] = logical_json(da_raw) if da_raw is not None else None
        row[f"{field}_en_json"] = logical_json(en_raw) if en_raw is not None else None
        row[f"{field}_provenance"] = provenance
        row[f"{field}_status"] = status
        if field == "colortemp" and (
            (isinstance(da_raw, str) and da_raw.casefold() == "infinity")
            or (isinstance(en_raw, str) and en_raw.casefold() == "infinity")
        ):
            flags.append("COLORTEMP_NONFINITE_SOURCE")
    if any(row[field] is None for field in VISUAL_FIELDS):
        flags.append("VISUAL_FIELDS_PARTIAL")
    return flags


def _canonical_row(
    pair: dict[str, Any], shared_object_numbers: set[str], colortemp_median: float,
    colortemp_mad: float,
) -> dict[str, Any]:
    da = json.loads(pair["da_record_json"]) if pair["da_record_json"] else None
    en = json.loads(pair["en_record_json"]) if pair["en_record_json"] else None
    da_entity_id = da.get("id") if da else None
    en_entity_id = en.get("id") if en else None
    entity_id = resolve_smk_entity_id(da_entity_id, en_entity_id)
    if pair["smk_entity_id"] != entity_id:
        raise ValueError("Joined SMK entity id does not match source record id")
    row: dict[str, Any] = {
        "canonical_schema_version": CANONICAL_VERSION,
        "smk_entity_id": entity_id,
        "source_row_id_da": pair["da_source_row_id"],
        "source_row_id_en": pair["en_source_row_id"],
        "present_in_da": da is not None,
        "present_in_en": en is not None,
        "source_manifest_sha256_da": pair["da_manifest_sha"],
        "source_manifest_sha256_en": pair["en_manifest_sha"],
        "source_file_sha256_da": pair["da_file_sha"],
        "source_file_sha256_en": pair["en_file_sha"],
    }
    da_object_number = _raw_value(da, "object_number")
    en_object_number = _raw_value(en, "object_number")
    object_number, provenance, status = resolve_scalar(da_object_number, en_object_number)
    row.update({
        "object_number": object_number,
        "object_number_da": da_object_number,
        "object_number_en": en_object_number,
        "object_number_provenance": provenance,
        "object_number_status": status,
    })
    _localized_fields(row, da, en)

    da_public = _raw_value(da, "public_domain")
    en_public = _raw_value(en, "public_domain")
    public_domain, public_provenance, public_status = resolve_scalar(da_public, en_public)
    row.update({
        "public_domain": public_domain,
        "public_domain_da": da_public,
        "public_domain_en": en_public,
        "public_domain_provenance": public_provenance,
        "public_domain_status": public_status,
    })

    da_rights = _raw_value(da, "rights")
    en_rights = _raw_value(en, "rights")
    da_semantic = rights_semantic(da_rights)
    en_semantic = rights_semantic(en_rights)
    if da is not None and en is not None and da_semantic == en_semantic:
        rights_value, rights_provenance, rights_status = da_semantic, "both", "semantic_agreement"
    elif da is not None and en is None:
        rights_value, rights_provenance, rights_status = da_semantic, "da", "single_source"
    elif en is not None and da is None:
        rights_value, rights_provenance, rights_status = en_semantic, "en", "single_source"
    else:
        rights_value, rights_provenance, rights_status = None, "conflict", "conflict"
    row.update({
        "rights_da": da_rights,
        "rights_en": en_rights,
        "rights_semantic": rights_value,
        "rights_semantic_da": da_semantic if da is not None else None,
        "rights_semantic_en": en_semantic if en is not None else None,
        "rights_provenance": rights_provenance,
        "rights_status": rights_status,
    })

    da_colors = _raw_value(da, "colors") if isinstance(_raw_value(da, "colors"), list) else None
    en_colors = _raw_value(en, "colors") if isinstance(_raw_value(en, "colors"), list) else None
    colors, colors_provenance, colors_status = resolve_scalar(da_colors, en_colors)
    row.update({
        "colors": colors,
        "colors_da": da_colors,
        "colors_en": en_colors,
        "colors_provenance": colors_provenance,
        "colors_status": colors_status,
    })

    quality_flags = _visual_fields(row, da, en)
    if is_extreme_colortemp(row["colortemp"], colortemp_median, colortemp_mad):
        quality_flags.append("COLORTEMP_EXTREME")

    da_bundle = image_bundle(da)
    en_bundle = image_bundle(en)
    canonical_bundle, image_provenance, image_status = resolve_image_bundle(da_bundle, en_bundle)
    row.update({
        "image_bundle_status": image_status,
        "image_bundle_provenance": image_provenance,
        "image_bundle_complete": image_bundle_complete(canonical_bundle),
        "image_bundle_da_json": logical_json(da_bundle) if da_bundle is not None else None,
        "image_bundle_en_json": logical_json(en_bundle) if en_bundle is not None else None,
    })
    for key in IMAGE_KEYS:
        row[key] = canonical_bundle.get(key) if canonical_bundle else None

    observations = normalize_dimension_observations(da, "da", pair["da_source_row_id"])
    observations += normalize_dimension_observations(en, "en", pair["en_source_row_id"])
    slots, dimension_conflicts, conflict_candidates = dimension_slots(observations)
    row.update(slots)
    row["dimension_observations"] = observations
    row["dimension_conflict_slots"] = dimension_conflicts
    row["dimension_conflict_candidates"] = conflict_candidates
    row["has_net_width"] = row["net_width_cm"] is not None
    row["has_net_height"] = row["net_height_cm"] is not None
    row["has_2d_physical_geometry"] = row["has_net_width"] and row["has_net_height"]
    row["has_3d_physical_geometry"] = (
        row["has_2d_physical_geometry"] and row["net_depth_cm"] is not None
    )
    row["has_any_physical_dimension"] = any(value is not None for value in slots.values())

    def previous_candidate(record: dict[str, Any] | None) -> bool:
        return bool(
            record and record.get("public_domain") is True and record.get("has_image") is True
            and (record.get("image_native") or record.get("image_thumbnail") or record.get("image_iiif_id"))
        )

    row["previous_public_visual_candidate"] = previous_candidate(da) or previous_candidate(en)

    if da is None or en is None:
        quality_flags.append("SOURCE_LANGUAGE_MISSING")
    if object_number in shared_object_numbers:
        quality_flags.append("OBJECT_NUMBER_SHARED")
    if dimension_conflicts:
        quality_flags.append("DIMENSION_CONFLICT")
    quality_flags.append(image_status)
    unresolved = any(status_value == "conflict" for status_value in (
        status, public_status, rights_status, colors_status,
        *(row[f"{field}_status"] for field in VISUAL_FIELDS),
    ))
    if unresolved:
        quality_flags.append("CANONICALIZATION_UNRESOLVED")
    row["quality_flags"] = sorted(set(quality_flags))
    included, reasons = corpus_membership(row)
    row["corpus_smk_public_visual_v1"] = included
    row["corpus_exclusion_reasons"] = reasons
    return row


def _colortemp_parameters(source_paths: tuple[Path, Path]) -> tuple[float, float, int]:
    values_by_entity: dict[str, float] = {}
    for source_path in source_paths:
        parquet = pq.ParquetFile(source_path)
        for batch in parquet.iter_batches(columns=["smk_source_id", "visual_json"], batch_size=10_000):
            for row in batch.to_pylist():
                if row["smk_source_id"] in values_by_entity:
                    continue
                visual = json.loads(row["visual_json"])
                number, _ = visual_number(visual, "colortemp")
                if number is not None:
                    values_by_entity[row["smk_source_id"]] = number
    values = list(values_by_entity.values())
    median, mad = robust_colortemp_parameters(values)
    return median, mad, len(values)


def _shared_object_numbers(connection: duckdb.DuckDBPyConnection, da_path: str, en_path: str) -> set[str]:
    query = f"""
        SELECT object_number
        FROM (
          SELECT smk_source_id, object_number FROM read_parquet('{da_path}')
          UNION
          SELECT smk_source_id, object_number FROM read_parquet('{en_path}')
        )
        WHERE object_number IS NOT NULL
        GROUP BY object_number
        HAVING count(DISTINCT smk_source_id) > 1
    """
    return {row[0] for row in connection.execute(query).fetchall()}


def run(root: Path) -> dict[str, Any]:
    da_path = (root / "data" / "interim" / "source_da.parquet").resolve()
    en_path = (root / "data" / "interim" / "source_en.parquet").resolve()
    processed = root / "data" / "processed"
    reports = root / "data" / "reports"
    processed.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect()
    da_sql = da_path.as_posix().replace("'", "''")
    en_sql = en_path.as_posix().replace("'", "''")
    shared_object_numbers = _shared_object_numbers(connection, da_sql, en_sql)
    colortemp_median, colortemp_mad, colortemp_count = _colortemp_parameters((da_path, en_path))

    schema = _schema()
    da_metadata = pq.ParquetFile(da_path).schema_arrow.metadata or {}
    en_metadata = pq.ParquetFile(en_path).schema_arrow.metadata or {}
    manifest_sha = da_metadata[b"smk.source_manifest_sha256"].decode()
    if en_metadata[b"smk.source_manifest_sha256"].decode() != manifest_sha:
        raise ValueError("DA/EN source Parquets reference different source manifests")
    metadata = {
        b"smk.canonical_schema_version": CANONICAL_VERSION.encode(),
        b"smk.source_manifest_sha256": manifest_sha.encode(),
        b"smk.corpus_rule": b"smk-public-visual-v1",
    }
    artwork_writer = pq.ParquetWriter(processed / "artworks.parquet", schema.with_metadata(metadata), compression="zstd")
    corpus_writer = pq.ParquetWriter(
        processed / "smk-public-visual-v1.parquet", schema.with_metadata(metadata), compression="zstd",
    )
    membership_writer = pq.ParquetWriter(
        reports / "corpus-membership.parquet", MEMBERSHIP_SCHEMA.with_metadata(metadata), compression="zstd",
    )

    query = f"""
      SELECT
        coalesce(da.smk_source_id, en.smk_source_id) AS smk_entity_id,
        da.source_row_id AS da_source_row_id,
        en.source_row_id AS en_source_row_id,
        da.source_manifest_sha256 AS da_manifest_sha,
        en.source_manifest_sha256 AS en_manifest_sha,
        da.source_file_sha256 AS da_file_sha,
        en.source_file_sha256 AS en_file_sha,
        da.source_record_json AS da_record_json,
        en.source_record_json AS en_record_json
      FROM read_parquet('{da_sql}') da
      FULL OUTER JOIN read_parquet('{en_sql}') en
        ON da.smk_source_id = en.smk_source_id
      ORDER BY smk_entity_id
    """
    reader = connection.execute(query).to_arrow_reader(1_000)
    counters: dict[str, Counter[str]] = {
        "pairing": Counter(), "images": Counter(), "rights": Counter(), "quality": Counter(),
        "exclusions": Counter(), "dimension_slots": Counter(),
    }
    object_groups: dict[str, list[str]] = defaultdict(list)
    corpus_entities: set[str] = set()
    total = 0
    included_count = 0
    corpus_missing_2d = 0
    corpus_visual_partial = 0
    corpus_colortemp_flags = 0
    previous_candidate_count = 0
    previous_candidate_corpus_overlap = 0
    corpus_missing_any_physical = 0
    corpus_missing_visual_fields: Counter[str] = Counter()
    try:
        for batch in reader:
            artwork_rows: list[dict[str, Any]] = []
            corpus_rows: list[dict[str, Any]] = []
            membership_rows: list[dict[str, Any]] = []
            for pair in batch.to_pylist():
                row = _canonical_row(pair, shared_object_numbers, colortemp_median, colortemp_mad)
                total += 1
                if row["present_in_da"] and row["present_in_en"]:
                    counters["pairing"]["both"] += 1
                elif row["present_in_da"]:
                    counters["pairing"]["da_only"] += 1
                else:
                    counters["pairing"]["en_only"] += 1
                if row["object_number_status"] == "conflict":
                    counters["pairing"]["object_number_conflict"] += 1
                counters["images"][row["image_bundle_status"]] += 1
                counters["rights"][row["rights_semantic"] or "CONFLICT"] += 1
                for flag in row["quality_flags"]:
                    counters["quality"][flag] += 1
                for reason in row["corpus_exclusion_reasons"]:
                    counters["exclusions"][reason] += 1
                for part in SUPPORTED_PARTS:
                    for axis in SUPPORTED_AXES:
                        if row[f"{part}_{axis}_cm"] is not None:
                            counters["dimension_slots"][f"{part}_{axis}_cm"] += 1
                if row["object_number"]:
                    object_groups[row["object_number"]].append(row["smk_entity_id"])
                if row["previous_public_visual_candidate"]:
                    previous_candidate_count += 1
                if row["corpus_smk_public_visual_v1"]:
                    included_count += 1
                    corpus_entities.add(row["smk_entity_id"])
                    corpus_rows.append(row)
                    if not row["has_2d_physical_geometry"]:
                        corpus_missing_2d += 1
                    if not row["has_any_physical_dimension"]:
                        corpus_missing_any_physical += 1
                    if "VISUAL_FIELDS_PARTIAL" in row["quality_flags"]:
                        corpus_visual_partial += 1
                    for field in VISUAL_FIELDS:
                        if row[field] is None:
                            corpus_missing_visual_fields[field] += 1
                    if any(flag.startswith("COLORTEMP_") for flag in row["quality_flags"]):
                        corpus_colortemp_flags += 1
                    if row["previous_public_visual_candidate"]:
                        previous_candidate_corpus_overlap += 1
                artwork_rows.append(row)
                membership_rows.append({
                    "smk_entity_id": row["smk_entity_id"],
                    "object_number": row["object_number"],
                    "included": row["corpus_smk_public_visual_v1"],
                    "exclusion_reasons": row["corpus_exclusion_reasons"],
                    "quality_flags": row["quality_flags"],
                })
            artwork_writer.write_table(pa.Table.from_pylist(artwork_rows, schema=schema))
            membership_writer.write_table(pa.Table.from_pylist(membership_rows, schema=MEMBERSHIP_SCHEMA))
            if corpus_rows:
                corpus_writer.write_table(pa.Table.from_pylist(corpus_rows, schema=schema))
    finally:
        artwork_writer.close()
        corpus_writer.close()
        membership_writer.close()
        connection.close()

    group_rows: list[dict[str, Any]] = []
    corpus_shared_groups = 0
    corpus_shared_entities = 0
    for object_number, entity_ids in sorted(object_groups.items()):
        sorted_ids = sorted(entity_ids)
        corpus_members = sum(entity_id in corpus_entities for entity_id in sorted_ids)
        if len(sorted_ids) > 1 and corpus_members:
            corpus_shared_groups += 1
            corpus_shared_entities += corpus_members
        group_rows.append({
            "object_number": object_number,
            "canonical_entity_ids": sorted_ids,
            "group_size": len(sorted_ids),
            "group_classification": (
                "multiple_smk_entities_same_object_number" if len(sorted_ids) > 1 else "unique"
            ),
            "ambiguity_flag": len(sorted_ids) > 1,
            "corpus_member_count": corpus_members,
        })
    pq.write_table(
        pa.Table.from_pylist(group_rows, schema=GROUP_SCHEMA),
        processed / "object-number-groups.parquet", compression="zstd",
    )
    summary = {
        "canonical_schema_version": CANONICAL_VERSION,
        "source_manifest_sha256": manifest_sha,
        "canonical_entity_count": total,
        "pairing": dict(counters["pairing"]),
        "object_number_groups": {
            "total": len(group_rows),
            "shared_groups": len(shared_object_numbers),
            "largest_group": max(len(ids) for ids in object_groups.values()),
            "shared_groups_with_corpus_members": corpus_shared_groups,
            "corpus_members_in_shared_groups": corpus_shared_entities,
        },
        "dimensions": {
            "entities_with_conflicts": counters["quality"]["DIMENSION_CONFLICT"],
            "entities_with_net_width": counters["dimension_slots"]["net_width_cm"],
            "entities_with_net_height": counters["dimension_slots"]["net_height_cm"],
            "slot_success_counts": dict(counters["dimension_slots"]),
        },
        "images": dict(counters["images"]),
        "rights": dict(counters["rights"]),
        "quality_flags": dict(counters["quality"]),
        "colortemp_extreme_rule": {
            "rule": "absolute robust z-score > 10 using median and MAD",
            "entity_numeric_count": colortemp_count,
            "median": colortemp_median,
            "mad": colortemp_mad,
        },
        "corpus": {
            "name": "smk-public-visual-v1",
            "included": included_count,
            "excluded": total - included_count,
            "exclusion_reason_counts": dict(counters["exclusions"]),
            "previous_public_visual_candidate_count": previous_candidate_count,
            "overlap_with_previous_public_visual_candidates": previous_candidate_corpus_overlap,
            "included_without_any_normalized_physical_dimension": corpus_missing_any_physical,
            "included_without_2d_net_geometry": corpus_missing_2d,
            "included_with_partial_visual_fields": corpus_visual_partial,
            "included_missing_visual_field_counts": dict(corpus_missing_visual_fields),
            "included_with_colortemp_quality_flags": corpus_colortemp_flags,
        },
    }
    (reports / "milestone2-summary.json").write_text(
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

"""Pure, deterministic Milestone 2 canonicalization rules."""

from __future__ import annotations

import math
import statistics
import unicodedata
from collections import defaultdict
from typing import Any

from smk_playground.ingest.source import parse_strict_number

PDM_URL = "https://creativecommons.org/publicdomain/mark/1.0/"
CC0_URL = "https://creativecommons.org/publicdomain/zero/1.0/"
SMK_POLICY_URLS = {
    "https://www.smk.dk/section/brug-af-museets-materiale/",
    "https://www.smk.dk/en/section/use-of-smk-material/",
}

PART_ALIASES = {
    "netto": "net",
    "nettomål": "net",
    "brutto": "gross",
    "bruttomål": "gross",
    "bladmål": "sheet",
    "plademål": "plate",
    "monteringsmål": "mount",
    "billedmål": "image",
    "papirmål": "paper",
}
TYPE_ALIASES = {
    "bredde": "width",
    "width": "width",
    "højde": "height",
    "height": "height",
    "dybde": "depth",
    "depth": "depth",
    "diameter": "diameter",
    "længde": "length",
    "length": "length",
}
UNIT_TO_CM = {
    "millimeter": 0.1,
    "milimeter": 0.1,
    "mm": 0.1,
    "centimeter": 1.0,
    "cm": 1.0,
}
SUPPORTED_PARTS = ("net", "gross", "sheet", "plate", "mount", "image", "paper")
SUPPORTED_AXES = ("width", "height", "depth", "diameter", "length")
IMAGE_KEYS = (
    "has_image", "image_iiif_id", "image_iiif_info", "image_width", "image_height",
    "image_thumbnail", "image_native", "image_mime_type", "image_cropped",
    "image_orientation", "image_hq",
)


def resolve_smk_entity_id(da_id: str | None, en_id: str | None) -> str:
    """Pair languages only when their stable SMK source entity IDs agree."""
    if da_id and en_id and da_id != en_id:
        raise ValueError(f"Cannot pair different SMK ids: {da_id!r} != {en_id!r}")
    entity_id = da_id or en_id
    if not entity_id:
        raise ValueError("Canonical entity requires an SMK id")
    return entity_id


def normalize_vocabulary_token(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    token = unicodedata.normalize("NFC", value.strip()).casefold()
    return token.replace("maal", "mål")


def rights_semantic(value: Any) -> str:
    if value == PDM_URL:
        return "PDM"
    if value == CC0_URL:
        return "CC0"
    if value in SMK_POLICY_URLS:
        return "SMK_RESTRICTED_POLICY"
    return "UNKNOWN"


def resolve_scalar(da_value: Any, en_value: Any) -> tuple[Any, str, str]:
    """Return canonical value, provenance, and status without global language precedence."""
    if da_value == en_value and da_value is not None:
        return da_value, "both", "agreement"
    if da_value is not None and en_value is None:
        return da_value, "da", "single_source"
    if en_value is not None and da_value is None:
        return en_value, "en", "single_source"
    if da_value is None and en_value is None:
        return None, "none", "missing"
    return None, "conflict", "conflict"


def image_bundle(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if record is None:
        return None
    return {key: record.get(key) for key in IMAGE_KEYS}


def image_bundle_complete(bundle: dict[str, Any] | None) -> bool:
    if not bundle or bundle.get("has_image") is not True:
        return False
    width = bundle.get("image_width")
    height = bundle.get("image_height")
    return (
        isinstance(width, int) and not isinstance(width, bool) and width > 0
        and isinstance(height, int) and not isinstance(height, bool) and height > 0
        and isinstance(bundle.get("image_iiif_id"), str) and bool(bundle["image_iiif_id"])
        and bool(bundle.get("image_thumbnail") or bundle.get("image_native"))
    )


def resolve_image_bundle(
    da_bundle: dict[str, Any] | None, en_bundle: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, str, str]:
    da_complete = image_bundle_complete(da_bundle)
    en_complete = image_bundle_complete(en_bundle)
    if da_bundle == en_bundle and da_bundle is not None:
        status = "IMAGE_BUNDLE_OK" if da_complete else "IMAGE_BUNDLE_INCOMPLETE"
        return da_bundle, "both", status
    if da_complete and not en_complete:
        return da_bundle, "da", "IMAGE_BUNDLE_SINGLE_SOURCE"
    if en_complete and not da_complete:
        return en_bundle, "en", "IMAGE_BUNDLE_SINGLE_SOURCE"
    if da_complete and en_complete:
        return None, "conflict", "IMAGE_BUNDLE_CONFLICT"
    if da_bundle is not None and en_bundle is None:
        return da_bundle, "da", "IMAGE_BUNDLE_INCOMPLETE"
    if en_bundle is not None and da_bundle is None:
        return en_bundle, "en", "IMAGE_BUNDLE_INCOMPLETE"
    return None, "none", "IMAGE_BUNDLE_INCOMPLETE"


def normalize_dimension_observations(
    record: dict[str, Any] | None, language: str, source_row_id: str | None,
) -> list[dict[str, Any]]:
    if record is None:
        return []
    dimensions = record.get("dimensions")
    if not isinstance(dimensions, list):
        return []
    output: list[dict[str, Any]] = []
    for item in dimensions:
        if not isinstance(item, dict):
            continue
        original_part = item.get("part")
        original_type = item.get("type")
        original_unit = item.get("unit")
        original_value = item.get("value")
        part = PART_ALIASES.get(normalize_vocabulary_token(original_part) or "")
        axis = TYPE_ALIASES.get(normalize_vocabulary_token(original_type) or "")
        unit_token = normalize_vocabulary_token(original_unit)
        factor = UNIT_TO_CM.get(unit_token or "")
        number, number_status = parse_strict_number(original_value)
        if part and axis and factor is not None and number is not None:
            value_cm = number * factor
            status = "normalized"
        elif axis is None and normalize_vocabulary_token(original_type) in {
            "vægt", "weight", "spilletid", "playing time", "bruttoregisterton",
        }:
            value_cm = None
            status = "non_geometric"
        else:
            value_cm = None
            status = f"unmapped_or_{number_status}"
        output.append({
            "part_canonical": part,
            "type_canonical": axis,
            "unit_canonical": "cm" if value_cm is not None else None,
            "value_canonical": value_cm,
            "original_language": language,
            "original_part": None if original_part is None else str(original_part),
            "original_type": None if original_type is None else str(original_type),
            "original_unit": None if original_unit is None else str(original_unit),
            "original_value": None if original_value is None else str(original_value),
            "source_row_id": source_row_id,
            "status": status,
        })
    return output


def dimension_slots(
    observations: list[dict[str, Any]],
) -> tuple[dict[str, float | None], list[str], list[dict[str, Any]]]:
    candidates: dict[str, set[float]] = defaultdict(set)
    candidate_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for observation in observations:
        part = observation["part_canonical"]
        axis = observation["type_canonical"]
        value = observation["value_canonical"]
        if part in SUPPORTED_PARTS and axis in SUPPORTED_AXES and value is not None:
            slot = f"{part}_{axis}_cm"
            candidates[slot].add(round(float(value), 12))
            candidate_rows[slot].append(observation)
    slots: dict[str, float | None] = {}
    conflicts: list[str] = []
    for part in SUPPORTED_PARTS:
        for axis in SUPPORTED_AXES:
            slot = f"{part}_{axis}_cm"
            values = candidates.get(slot, set())
            slots[slot] = next(iter(values)) if len(values) == 1 else None
            if len(values) > 1:
                conflicts.append(slot)
    conflict_candidates = [row for slot in conflicts for row in candidate_rows[slot]]
    return slots, conflicts, conflict_candidates


def visual_number(record: dict[str, Any] | None, field: str) -> tuple[float | None, str]:
    if record is None:
        return None, "missing"
    return parse_strict_number(record.get(field))


def robust_colortemp_parameters(values: list[float]) -> tuple[float, float]:
    finite = [value for value in values if math.isfinite(value)]
    median = statistics.median(finite)
    mad = statistics.median(abs(value - median) for value in finite)
    return median, mad


def is_extreme_colortemp(value: float | None, median: float, mad: float) -> bool:
    if value is None or not math.isfinite(value) or mad == 0:
        return False
    return abs(value - median) / (1.4826 * mad) > 10.0


def corpus_membership(row: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if "CANONICALIZATION_UNRESOLVED" in row["quality_flags"]:
        reasons.append("CANONICALIZATION_UNRESOLVED")
    if row["public_domain"] is not True:
        reasons.append("NOT_PUBLIC_DOMAIN")
    if row["rights_semantic"] not in {"PDM", "CC0"}:
        reasons.append("RIGHTS_NOT_OPEN")
    if row["image_bundle_status"] == "IMAGE_BUNDLE_CONFLICT":
        reasons.append("IMAGE_CONFLICT")
    if not row["image_bundle_complete"]:
        reasons.append("NO_USABLE_IMAGE")
    if not row["colors"]:
        reasons.append("NO_COLORS")
    return not reasons, reasons


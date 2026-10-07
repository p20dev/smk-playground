"""Bounded-memory loading and stable source-row helpers for SMK snapshots."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterator, Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

import ijson

HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
STRICT_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def iter_source_records(path: Path) -> Iterator[dict[str, Any]]:
    """Yield objects from the observed top-level array without loading the file."""
    with path.open("rb") as stream:
        for record in ijson.items(stream, "item", use_float=False):
            if not isinstance(record, dict):
                raise TypeError(f"Expected object at $[] in {path}")
            yield _normalize_decimal_numbers(record)


def _normalize_decimal_numbers(value: Any) -> Any:
    """Convert ijson Decimal values while retaining JSON number semantics."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, list):
        return [_normalize_decimal_numbers(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_decimal_numbers(item) for key, item in value.items()}
    return value


def logical_json(value: Any) -> str:
    """Return deterministic, logically lossless JSON for storage and hashing."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def logical_sha256(value: Any) -> str:
    return hashlib.sha256(logical_json(value).encode("utf-8")).hexdigest()


def source_row_id(language: str, record: Mapping[str, Any]) -> str:
    """Build a stable row ID from SMK's source id; never use array position."""
    smk_id = record.get("id")
    if isinstance(smk_id, str) and smk_id.strip():
        return f"smk:{language}:{smk_id.strip()}"
    stable_fallback = {
        "language": language,
        "object_number": record.get("object_number"),
        "record": record,
    }
    return f"sha256:{logical_sha256(stable_fallback)}"


def parse_strict_number(value: Any) -> tuple[float | None, str]:
    """Parse a finite number without silently accepting malformed text."""
    if isinstance(value, bool) or value is None:
        return None, "missing" if value is None else "invalid_type"
    if isinstance(value, (int, float)):
        number = float(value)
        return (number, "numeric") if math.isfinite(number) else (None, "non_finite")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None, "blank"
        if not STRICT_NUMBER_RE.fullmatch(text):
            return None, "malformed_text"
        number = float(text)
        return (number, "numeric_text") if math.isfinite(number) else (None, "non_finite")
    return None, "invalid_type"


def normalize_dimension_axis(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    token = value.strip().casefold()
    mapping = {
        "bredde": "width",
        "width": "width",
        "højde": "height",
        "hojde": "height",
        "height": "height",
        "dybde": "depth",
        "depth": "depth",
        "diameter": "diameter",
        "længde": "length",
        "laengde": "length",
        "length": "length",
    }
    return mapping.get(token)


def normalize_dimension_unit(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    token = value.strip().casefold().replace(".", "")
    mapping = {
        "millimeter": "mm",
        "millimetre": "mm",
        "mm": "mm",
        "centimeter": "cm",
        "centimetre": "cm",
        "cm": "cm",
        "meter": "m",
        "metre": "m",
        "m": "m",
    }
    return mapping.get(token)


def normalized_dimensions(record: Mapping[str, Any]) -> list[tuple[str, str, str, float]]:
    """Create an audit-only localized comparison signature, not canonical dimensions."""
    output: list[tuple[str, str, str, float]] = []
    dimensions = record.get("dimensions")
    if not isinstance(dimensions, list):
        return output
    for item in dimensions:
        if not isinstance(item, dict):
            continue
        axis = normalize_dimension_axis(item.get("type"))
        unit = normalize_dimension_unit(item.get("unit"))
        number, status = parse_strict_number(item.get("value"))
        if axis and unit and number is not None and status in {"numeric", "numeric_text"}:
            part = str(item.get("part") or "").strip().casefold()
            output.append((part, axis, unit, number))
    return sorted(output)


"""Pure per-artwork feature extraction for artart-visual-features v1."""

from __future__ import annotations

import math
from typing import Any

from .color import ACHROMATIC_EPSILON, ConvertedColor, hex_to_oklab, oklab_to_oklch

PALETTE_SOURCE = "smk_bulk_colors"
PALETTE_WEIGHTING = "uniform"
ASPECT_MISMATCH_THRESHOLD = math.log(2.0)


def analytical_palette(source_colors: list[str] | None) -> tuple[list[dict[str, Any]], list[str]]:
    flags: list[str] = []
    if not source_colors:
        return [], ["PALETTE_EMPTY"]
    unique: list[tuple[int, str, str]] = []
    seen: set[str] = set()
    for source_rank, source_hex in enumerate(source_colors, start=1):
        canonical = source_hex.casefold()
        if canonical in seen:
            if "PALETTE_DUPLICATE_SOURCE_COLOR" not in flags:
                flags.append("PALETTE_DUPLICATE_SOURCE_COLOR")
            continue
        seen.add(canonical)
        unique.append((source_rank, source_hex, canonical))
    if not unique:
        return [], sorted({*flags, "PALETTE_EMPTY"})
    weight = 1.0 / len(unique)
    rows: list[dict[str, Any]] = []
    for palette_rank, (source_rank, source_hex, canonical) in enumerate(unique, start=1):
        converted = hex_to_oklab(canonical)
        rows.append(_palette_row(palette_rank, source_rank, source_hex, weight, converted))
    if all(row["oklch_h_deg"] is None for row in rows):
        flags.append("PALETTE_ACHROMATIC")
    return rows, sorted(flags)


def _palette_row(
    palette_rank: int,
    source_rank: int,
    source_hex: str,
    weight: float,
    color: ConvertedColor,
) -> dict[str, Any]:
    return {
        "palette_rank": palette_rank,
        "source_rank": source_rank,
        "source_hex": source_hex,
        "hex": color.hex,
        "weight": weight,
        "srgb_r": color.srgb_r,
        "srgb_g": color.srgb_g,
        "srgb_b": color.srgb_b,
        "oklab_l": color.oklab_l,
        "oklab_a": color.oklab_a,
        "oklab_b": color.oklab_b,
        "oklch_l": color.oklch_l,
        "oklch_c": color.oklch_c,
        "oklch_h_deg": color.oklch_h_deg,
    }


def _weighted_mean(values: list[float], weights: list[float]) -> float:
    return math.fsum(weight * value for value, weight in zip(values, weights, strict=True))


def _weighted_stddev(values: list[float], weights: list[float], mean: float) -> float:
    variance = math.fsum(
        weight * (value - mean) ** 2 for value, weight in zip(values, weights, strict=True)
    )
    return math.sqrt(max(0.0, variance))


def palette_features(palette: list[dict[str, Any]]) -> tuple[dict[str, float | None], list[str]]:
    if not palette:
        return {
            "centroid_l": None, "centroid_a": None, "centroid_b": None,
            "centroid_chroma": None, "centroid_hue_deg": None,
            "palette_entropy_01": None, "effective_palette_size": None,
            "palette_spread_oklab": None, "lightness_stddev": None,
            "chroma_stddev": None, "hue_concentration_01": None,
        }, ["PALETTE_EMPTY", "HUE_CONCENTRATION_UNAVAILABLE"]
    weights = [row["weight"] for row in palette]
    lightness = [row["oklab_l"] for row in palette]
    a_values = [row["oklab_a"] for row in palette]
    b_values = [row["oklab_b"] for row in palette]
    chroma = [row["oklch_c"] for row in palette]
    centroid_l = _weighted_mean(lightness, weights)
    centroid_a = _weighted_mean(a_values, weights)
    centroid_b = _weighted_mean(b_values, weights)
    _, centroid_chroma, centroid_hue = oklab_to_oklch(centroid_l, centroid_a, centroid_b)
    entropy = -math.fsum(weight * math.log(weight) for weight in weights if weight > 0)
    n = len(palette)
    entropy_01 = 0.0 if n <= 1 else min(1.0, max(0.0, entropy / math.log(n)))
    spread = math.fsum(
        row["weight"] * math.sqrt(
            (row["oklab_l"] - centroid_l) ** 2
            + (row["oklab_a"] - centroid_a) ** 2
            + (row["oklab_b"] - centroid_b) ** 2
        )
        for row in palette
    )
    mean_chroma = _weighted_mean(chroma, weights)
    hue_x = 0.0
    hue_y = 0.0
    chromatic_weight = 0.0
    for row in palette:
        if row["oklch_h_deg"] is None or row["oklch_c"] < ACHROMATIC_EPSILON:
            continue
        effective_weight = row["weight"] * row["oklch_c"]
        radians = math.radians(row["oklch_h_deg"])
        hue_x += effective_weight * math.cos(radians)
        hue_y += effective_weight * math.sin(radians)
        chromatic_weight += effective_weight
    flags: list[str] = []
    if chromatic_weight < ACHROMATIC_EPSILON:
        hue_concentration = None
        flags.extend(["PALETTE_ACHROMATIC", "HUE_CONCENTRATION_UNAVAILABLE"])
    else:
        hue_concentration = min(1.0, math.hypot(hue_x, hue_y) / chromatic_weight)
    if centroid_hue is None:
        flags.append("CENTROID_ACHROMATIC")
    return {
        "centroid_l": centroid_l,
        "centroid_a": centroid_a,
        "centroid_b": centroid_b,
        "centroid_chroma": centroid_chroma,
        "centroid_hue_deg": centroid_hue,
        "palette_entropy_01": entropy_01,
        "effective_palette_size": math.exp(entropy),
        "palette_spread_oklab": spread,
        "lightness_stddev": _weighted_stddev(lightness, weights, centroid_l),
        "chroma_stddev": _weighted_stddev(chroma, weights, mean_chroma),
        "hue_concentration_01": hue_concentration,
    }, sorted(set(flags))


def geometry_features(canonical: dict[str, Any]) -> tuple[dict[str, float | int | None], list[str]]:
    width = canonical.get("net_width_cm")
    height = canonical.get("net_height_cm")
    image_width = canonical.get("image_width")
    image_height = canonical.get("image_height")
    valid_physical = all(
        isinstance(value, (int, float)) and math.isfinite(value) and value > 0
        for value in (width, height)
    )
    valid_image = all(
        isinstance(value, int) and not isinstance(value, bool) and value > 0
        for value in (image_width, image_height)
    )
    flags: list[str] = []
    if valid_physical:
        area = width * height
        physical_aspect = width / height
    else:
        width = height = area = physical_aspect = None
        flags.append("PHYSICAL_GEOMETRY_MISSING")
    image_aspect = image_width / image_height if valid_image else None
    mismatch = (
        abs(math.log(physical_aspect / image_aspect))
        if physical_aspect is not None and image_aspect is not None else None
    )
    if (
        ASPECT_MISMATCH_THRESHOLD is not None and mismatch is not None
        and mismatch > ASPECT_MISMATCH_THRESHOLD
    ):
        flags.append("PHYSICAL_IMAGE_ASPECT_MISMATCH")
    return {
        "net_width_cm": width,
        "net_height_cm": height,
        "net_area_cm2": area,
        "net_aspect_ratio": physical_aspect,
        "log_net_width_cm": math.log(width) if width is not None else None,
        "log_net_height_cm": math.log(height) if height is not None else None,
        "log_net_area_cm2": math.log(area) if area is not None else None,
        "image_width_px": image_width if valid_image else None,
        "image_height_px": image_height if valid_image else None,
        "image_aspect_ratio": image_aspect,
        "aspect_mismatch_log": mismatch,
    }, flags


def extract_artwork(canonical: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_colors = canonical.get("colors")
    palette, palette_flags = analytical_palette(source_colors)
    calculated, calculated_flags = palette_features(palette)
    geometry, geometry_flags = geometry_features(canonical)
    feature_flags = sorted({*palette_flags, *calculated_flags, *geometry_flags})
    canonical_flags = sorted(canonical.get("quality_flags") or [])
    feature = {
        "smk_entity_id": canonical["smk_entity_id"],
        "object_number": canonical.get("object_number"),
        "palette_source": PALETTE_SOURCE,
        "palette_weighting": PALETTE_WEIGHTING,
        "palette_source_size": len(source_colors or []),
        "palette_analytic_size": len(palette),
        "source_palette": source_colors,
        "first_palette_color_hex": source_colors[0] if source_colors else None,
        "palette_source_order_preserved": True,
        **calculated,
        "smk_brightness": canonical.get("brightness"),
        "smk_contrast": canonical.get("contrast"),
        "smk_saturation": canonical.get("saturation"),
        "smk_entropy": canonical.get("entropy"),
        "smk_colortemp": canonical.get("colortemp"),
        **geometry,
        "canonical_quality_flags": canonical_flags,
        "feature_quality_flags": feature_flags,
        "quality_flags": sorted({*canonical_flags, *feature_flags}),
    }
    return feature, palette

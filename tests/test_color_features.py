import math

import pytest

from smk_playground.features.color import hex_to_oklab, oklab_to_oklch
from smk_playground.features.extract import (
    analytical_palette,
    extract_artwork,
    palette_features,
)


@pytest.mark.parametrize(
    ("hex_value", "expected"),
    [
        ("#ff0000", (0.62795536, 0.22486306, 0.12584630)),
        ("#00ff00", (0.86643961, -0.23388757, 0.17949848)),
        ("#0000ff", (0.45201372, -0.03245698, -0.31152815)),
    ],
)
def test_known_srgb_oklab_reference_colors(hex_value: str, expected: tuple[float, ...]) -> None:
    color = hex_to_oklab(hex_value)
    assert (color.oklab_l, color.oklab_a, color.oklab_b) == pytest.approx(expected, abs=2e-7)


def test_achromatic_oklch_hue_is_null() -> None:
    assert oklab_to_oklch(0.5, 0.0, 0.0) == (0.5, 0.0, None)
    assert hex_to_oklab("#ffffff").oklch_h_deg is None


def test_uniform_weights_and_duplicate_source_colors() -> None:
    palette, flags = analytical_palette(["#FF0000", "#ff0000", "#0000ff"])
    assert len(palette) == 2
    assert math.fsum(row["weight"] for row in palette) == pytest.approx(1.0)
    assert [row["source_rank"] for row in palette] == [1, 3]
    assert flags == ["PALETTE_DUPLICATE_SOURCE_COLOR"]


def test_one_color_palette_boundaries() -> None:
    palette, _ = analytical_palette(["#ff0000"])
    features, _ = palette_features(palette)
    assert features["palette_entropy_01"] == 0.0
    assert features["effective_palette_size"] == pytest.approx(1.0)
    assert features["palette_spread_oklab"] == pytest.approx(0.0)
    assert features["hue_concentration_01"] == pytest.approx(1.0)


def test_two_color_centroid_entropy_spread_and_hue() -> None:
    palette, _ = analytical_palette(["#ff0000", "#0000ff"])
    features, _ = palette_features(palette)
    red = hex_to_oklab("#ff0000")
    blue = hex_to_oklab("#0000ff")
    assert features["centroid_l"] == pytest.approx((red.oklab_l + blue.oklab_l) / 2)
    assert features["centroid_a"] == pytest.approx((red.oklab_a + blue.oklab_a) / 2)
    assert features["palette_entropy_01"] == pytest.approx(1.0)
    assert features["effective_palette_size"] == pytest.approx(2.0)
    assert 0 < features["palette_spread_oklab"] < 1
    assert 0 <= features["hue_concentration_01"] <= 1


def test_geometry_logs_and_null_propagation_are_deterministic() -> None:
    canonical = {
        "smk_entity_id": "entity", "object_number": "A1", "colors": ["#ffffff"],
        "net_width_cm": 10.0, "net_height_cm": 20.0,
        "image_width": 100, "image_height": 200, "quality_flags": [],
    }
    first, _ = extract_artwork(canonical)
    second, _ = extract_artwork(dict(canonical))
    assert first == second
    assert first["net_area_cm2"] == 200.0
    assert first["log_net_area_cm2"] == pytest.approx(math.log(200.0))
    canonical["net_width_cm"] = None
    missing, _ = extract_artwork(canonical)
    assert missing["net_area_cm2"] is None
    assert "PHYSICAL_GEOMETRY_MISSING" in missing["feature_quality_flags"]


def test_conservative_aspect_mismatch_flag() -> None:
    canonical = {
        "smk_entity_id": "entity", "object_number": "A1", "colors": ["#ffffff"],
        "net_width_cm": 10.0, "net_height_cm": 10.0,
        "image_width": 100, "image_height": 300, "quality_flags": [],
    }
    feature, _ = extract_artwork(canonical)
    assert feature["aspect_mismatch_log"] == pytest.approx(math.log(3.0))
    assert "PHYSICAL_IMAGE_ASPECT_MISMATCH" in feature["feature_quality_flags"]

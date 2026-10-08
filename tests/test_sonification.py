"""Focused invariants for deterministic sonification profiles."""

import pytest

from smk_playground.sonification.profiles import (
    hue_pitch_class,
    palette_arpeggio,
    physical_artwork_tone,
    weighted_color_tone,
)


def feature(**updates):
    values = {
        "has_weighted_palette_v1": True,
        "centroid_hue_deg": 30.0,
        "centroid_l": 0.5,
        "centroid_chroma": 0.1,
        "dominant_color_weight": 0.4,
        "palette_spread_oklab": 0.15,
        "palette_entropy_01": 0.6,
        "hue_concentration_01": 0.7,
    }
    values.update(updates)
    return values


def test_hue_bins_and_explicit_achromatic_neutral():
    assert hue_pitch_class(0)[:2] == (0, "C")
    assert hue_pitch_class(30)[:2] == (1, "C#")
    assert hue_pitch_class(359)[:2] == (11, "B")
    assert hue_pitch_class(None) == (9, "A", "achromatic_neutral")


def test_weighted_tone_is_deterministic_and_bounded():
    first = weighted_color_tone(feature())
    assert first == weighted_color_tone(feature())
    assert first["note"] == "C#"
    assert 36 <= first["midi"] <= 84
    assert 0 <= first["velocity"] <= 1


def test_physical_profile_requires_geometry_and_large_works_sound_lower():
    assert not physical_artwork_tone(feature(), {})["available"]
    small = physical_artwork_tone(
        feature(), {"log_net_area_cm2_percentile_01": 0.1, "log_net_aspect_ratio": -0.5}
    )
    large = physical_artwork_tone(
        feature(), {"log_net_area_cm2_percentile_01": 0.9, "log_net_aspect_ratio": 0.5}
    )
    assert large["midi"] < small["midi"]
    assert small["stereo_pan"] == pytest.approx(-large["stereo_pan"])


def test_palette_arpeggio_orders_by_weight_then_rank():
    palette = [
        {"palette_rank": 2, "hex": "#aaaaaa", "weight": 0.3, "oklch_h_deg": None, "oklab_l": 0.5},
        {"palette_rank": 1, "hex": "#ff0000", "weight": 0.7, "oklch_h_deg": 0.0, "oklab_l": 0.7},
    ]
    notes = palette_arpeggio(palette)["notes"]
    assert [note["hex"] for note in notes] == ["#ff0000", "#aaaaaa"]
    assert notes[1]["pitch_source"] == "achromatic_neutral"

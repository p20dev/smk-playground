"""Deterministic artistic mappings from artwork features to browser-audio parameters."""

from __future__ import annotations

import math
from typing import Any

PROFILE_VERSION = "1.0.0"
PITCH_CLASSES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return min(high, max(low, value))


def hue_pitch_class(hue_degrees: float | None) -> tuple[int, str, str]:
    if hue_degrees is None:
        return 9, "A", "achromatic_neutral"
    index = int((hue_degrees % 360.0) // 30.0)
    return index, PITCH_CLASSES[index], "weighted_centroid_hue"


def nearest_midi(target: float, pitch_class: int) -> int:
    candidates = [midi for midi in range(36, 85) if midi % 12 == pitch_class]
    return min(candidates, key=lambda midi: (abs(midi - target), midi))


def midi_frequency(midi: int) -> float:
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def _shared_timbre(feature: dict[str, Any]) -> dict[str, float]:
    return {
        "velocity": clamp(0.28 + 4.2 * float(feature.get("centroid_chroma") or 0.0), 0.25, 0.92),
        "attack": 0.08 + 0.18 * (1.0 - float(feature.get("dominant_color_weight") or 0.0)),
        "release": 0.65 + 1.35 * float(feature.get("dominant_color_weight") or 0.0),
        "harmonic_richness": clamp(float(feature.get("palette_spread_oklab") or 0.0) / 0.35),
        "noise_amount": 0.10 * clamp(float(feature.get("palette_entropy_01") or 0.0)),
        "tonal_purity": clamp(float(feature.get("hue_concentration_01") or 0.0)),
    }


def weighted_color_tone(feature: dict[str, Any]) -> dict[str, Any]:
    available = bool(feature.get("has_weighted_palette_v1"))
    if not available:
        return {"profile": "weighted-color-tone-v1", "version": PROFILE_VERSION,
                "available": False, "reason": "weighted palette unavailable"}
    pitch_class, note, pitch_source = hue_pitch_class(feature.get("centroid_hue_deg"))
    lightness = clamp(float(feature["centroid_l"]))
    midi = nearest_midi(36.0 + 48.0 * lightness, pitch_class)
    return {
        "profile": "weighted-color-tone-v1", "version": PROFILE_VERSION, "available": True,
        "note": note, "octave": midi // 12 - 1, "midi": midi,
        "frequency_hz": midi_frequency(midi), "pitch_source": pitch_source,
        **_shared_timbre(feature),
        "stereo_pan": 0.0,
        "explanation": {
            "pitch": "weighted centroid hue; A is the explicit achromatic neutral",
            "register": "weighted centroid OKLab lightness mapped to MIDI 36–84",
            "timbre": "weighted chroma, spread, entropy, hue concentration, and dominant weight",
        },
    }


def physical_artwork_tone(feature: dict[str, Any], normalized: dict[str, Any]) -> dict[str, Any]:
    area_percentile = normalized.get("log_net_area_cm2_percentile_01")
    log_aspect = normalized.get("log_net_aspect_ratio")
    if not feature.get("has_weighted_palette_v1") or area_percentile is None or log_aspect is None:
        return {"profile": "physical-artwork-tone-v1", "version": PROFILE_VERSION,
                "available": False, "reason": "reliable physical Netto geometry unavailable"}
    pitch_class, note, pitch_source = hue_pitch_class(feature.get("centroid_hue_deg"))
    midi = nearest_midi(84.0 - 48.0 * clamp(float(area_percentile)), pitch_class)
    return {
        "profile": "physical-artwork-tone-v1", "version": PROFILE_VERSION, "available": True,
        "note": note, "octave": midi // 12 - 1, "midi": midi,
        "frequency_hz": midi_frequency(midi), "pitch_source": pitch_source,
        **_shared_timbre(feature),
        "stereo_pan": 0.6 * math.tanh(float(log_aspect)),
        "explanation": {
            "pitch": "weighted centroid hue; A is the explicit achromatic neutral",
            "register": "inverse physical log-area percentile: larger works sound lower",
            "stereo_pan": "subtle signed physical log-aspect mapping",
            "timbre": "weighted chroma, spread, entropy, hue concentration, and dominant weight",
        },
    }


def palette_arpeggio(palette: list[dict[str, Any]]) -> dict[str, Any]:
    notes = []
    for row in sorted(palette, key=lambda item: (-item["weight"], item["palette_rank"])):
        pitch_class, note, pitch_source = hue_pitch_class(row.get("oklch_h_deg"))
        midi = nearest_midi(48.0 + 24.0 * clamp(float(row["oklab_l"])), pitch_class)
        notes.append({
            "hex": row["hex"], "weight": row["weight"], "note": note,
            "octave": midi // 12 - 1, "midi": midi, "frequency_hz": midi_frequency(midi),
            "velocity": clamp(0.30 + 0.70 * row["weight"], 0.3, 0.9),
            "duration_seconds": 0.18 + 1.15 * row["weight"], "pitch_source": pitch_source,
        })
    return {"profile": "palette-arpeggio-v1", "version": PROFILE_VERSION,
            "available": bool(notes), "notes": notes,
            "explanation": "descending palette weight; hue→pitch, lightness→octave, weight→duration/intensity"}


def profile_manifest(input_hash: str) -> dict[str, Any]:
    return {
        "profile_set_version": PROFILE_VERSION, "input_feature_sha256": input_hash,
        "profiles": {
            "weighted-color-tone-v1": {
                "version": PROFILE_VERSION, "pitch": "floor(hue_deg/30) over C..B; achromatic=A",
                "register": "nearest matching pitch class to 36 + 48*centroid_l",
            },
            "physical-artwork-tone-v1": {
                "version": PROFILE_VERSION, "required": ["weighted palette", "physical Netto geometry"],
                "register": "nearest matching pitch class to 84 - 48*log-area percentile",
                "aspect": "stereo_pan = 0.6*tanh(log_net_aspect_ratio)",
            },
            "palette-arpeggio-v1": {
                "version": PROFILE_VERSION, "order": "weight descending, palette rank ascending",
                "mapping": "hue→pitch; lightness→octave; weight→duration and velocity",
            },
        },
    }

# Sonification v1

Sonification is an interpretive presentation layer, not an objective artwork feature. The API
returns deterministic synthesis parameters; sound is produced only after a user action by the
browser Web Audio API. The frozen profile set is `1.0.0` and is materialized as
`data/processed/sonification-profiles-v1.json`.

## Weighted color tone

`weighted-color-tone-v1` maps the enrichment-weighted OKLab centroid to one sustained tone:

- hue uses twelve equal 30-degree bins, `floor(hue / 30)`, mapped C through B;
- undefined achromatic hue maps explicitly to A and reports `achromatic_neutral`;
- centroid OKLab lightness sets a target register from MIDI 36 through 84, rounded to the nearest
  MIDI note in the selected pitch class;
- centroid chroma controls velocity, palette spread controls harmonic richness, normalized
  palette entropy controls a small noise component, hue concentration controls tonal purity, and
  dominant weight controls attack and release.

All controls are clamped to documented safe ranges in `sonification/profiles.py`.

## Physical artwork tone

`physical-artwork-tone-v1` uses the same hue and timbre mapping, but inverse log-area percentile
sets register: larger physical works sound lower. Signed log aspect ratio produces subtle stereo
pan via `0.6 * tanh(log_aspect)`. The profile is explicitly unavailable unless both a weighted
palette and reliable Netto width/height-derived normalized geometry exist. Pixel dimensions never
substitute for physical measurements.

## Palette arpeggio

`palette-arpeggio-v1` plays weighted palette entries in descending weight, with palette rank as a
stable tie-break. Each color maps hue to pitch class and lightness to octave; its weight controls
duration and velocity. The API includes the color, weight, note, MIDI number, frequency, duration,
and pitch-source explanation for every step.

These mappings are deliberately simple, explainable, and deterministic. They do not claim that an
artwork has an inherent sound or that musical distance is visual similarity.

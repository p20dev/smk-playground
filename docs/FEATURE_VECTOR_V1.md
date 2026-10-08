# Candidate feature vectors v1

`artwork-feature-vectors-v1.parquet` is a compact candidate dataset, not a similarity definition.
It contains one row per corpus entity, completeness flags and three fixed-size list columns. Exact
component order is embedded in the normalization profile and repeated below.

## `color_core_v1`

1. raw `centroid_l`
2. raw `centroid_a`
3. raw `centroid_b`
4. `palette_spread_oklab_robust_01`
5. `lightness_stddev_robust_01`
6. `chroma_stddev_robust_01`
7. natural `hue_concentration_01`

Raw OKLab coordinates deliberately preserve perceptual meaning. Centroid hue x/y are excluded to
avoid double-counting hue already represented by a/b.

## `visual_character_v1`

1. `smk_brightness_robust_01`
2. `smk_contrast_robust_01`
3. `smk_saturation_robust_01`
4. `smk_entropy_robust_01`

`smk_colortemp` remains available in the wide normalized table but is excluded here.

## `geometry_v1`

1. `log_net_width_cm_robust_01`
2. `log_net_height_cm_robust_01`
3. `log_net_area_cm2_robust_01`
4. `log_net_aspect_ratio_robust_01`

Geometry is optional and missing elements remain null. Raw area and raw aspect ratio are not vector
components. No family has weights, and the three families are not concatenated into a final
distance space. Later comparison may combine raw OKLab distance, normalized scalar distance,
palette-level distance and optional geometry under separately versioned similarity profiles.

Milestone 5 consumes explicit scalar columns rather than treating these lists as an opaque
universal vector. See `SIMILARITY_V1.md` for frozen component selection, scales and weights.


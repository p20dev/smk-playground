# Feature Specification v1

## Scope

Per-artwork feature extraction is deterministic and corpus-independent. Running the extractor for the same canonical inputs and extractor version must produce the same output regardless of how many other artworks exist.

## Palette input

Milestone 3 uses canonical SMK bulk `colors` and preserves source representation and order. The
bulk snapshots have no documented weights, so v1 uses explicitly labelled uniform analytical
weights (`1/n`) after deduplicating exact repeated hex values. Repetition is not interpreted as
weight.

For `colors_palette_weighted_s`, the observed format may contain repeated space-separated hex tokens. Parse defensively:

1. tokenize valid colours,
2. count each colour,
3. divide by total valid token count,
4. retain an explicit `weight_source`,
5. quality-flag malformed/partial input.

Uniform v1 weights are `palette_weighting = "uniform"`, never original SMK weights. Future
enrichment weights must retain separate provenance.

Canonical weights must satisfy approximately:

```text
weight >= 0
sum(weight) = 1
```

## Colour conversion

Use:

```text
sRGB -> linear RGB -> OKLab -> OKLCH
```

Use a single documented conversion implementation throughout v1 and test it against known reference colours.

## Perceptual colour centroid

Calculate the weighted mean in OKLab:

```text
L = Σ(wᵢLᵢ)
a = Σ(wᵢaᵢ)
b = Σ(wᵢbᵢ)
```

Store:

- `centroid_l`
- `centroid_a`
- `centroid_b`
- `centroid_chroma`
- `centroid_hue_deg`

Convert the centroid to OKLCH for chroma/hue. Hue is undefined for sufficiently achromatic centroids; use null rather than inventing a direction.

## Palette statistics

There is no `dominant_color_weight` in v1 because uniform weights do not measure image dominance.
The first source colour and preserved source order are available without claiming dominance.

### `palette_entropy_01`
Normalized Shannon entropy:

```text
H = -Σ(pᵢ ln pᵢ)
H01 = H / ln(n)
```

For `n <= 1`, define `palette_entropy_01 = 0.0`.

### `effective_palette_size`

```text
exp(H)
```

using unnormalized natural-log entropy.

### `palette_spread_oklab`
Weighted mean Euclidean OKLab distance from palette colours to the weighted centroid.

### `lightness_stddev`
Weighted standard deviation of OKLab L.

### `chroma_stddev`
Weighted standard deviation of OKLCH chroma.

### `hue_concentration_01`
Magnitude of a chroma-aware circular resultant where each hue contribution is weighted by:

```text
palette_weight * chroma
```

Return null when total chromatic mass is effectively zero.

## SMK-provided visual features

Preserve independently from our own calculations when present:

- `smk_brightness`
- `smk_contrast`
- `smk_saturation`
- `smk_colortemp`
- `smk_entropy`

SMK image entropy and our palette entropy are different concepts.

If multiple enrichment components/versions provide competing values, retain provenance and use an explicit precedence rule. Never silently mix components.

## Geometry

Canonical feature geometry:

- `net_width_cm`
- `net_height_cm`
- `net_area_cm2`
- `net_aspect_ratio`
- `image_aspect_ratio`
- `log_net_width_cm`
- `log_net_height_cm`
- `log_net_area_cm2`

Rules:

- prefer meaningful **Netto** dimensions over Brutto when both are available,
- normalize supported units to centimetres,
- do not infer physical dimensions from pixel dimensions,
- calculate area/aspect only where width + height are meaningful,
- calculate logarithms only for positive valid values.

## Aspect sanity check

For suitable 2D works where both physical and image aspect ratios exist, compare them using a symmetric log-ratio measure, e.g.:

```text
abs(log(physical_aspect / image_aspect))
```

Flag large mismatches; do not automatically “correct” either source.

## Quality/support fields

Include:

- `feature_schema_version`
- `extractor_version`
- source snapshot references
- enrichment component/version provenance when available
- `quality_flags`

Initial quality-flag vocabulary may include:

- `PALETTE_MISSING`
- `PALETTE_WEIGHTS_MISSING`
- `PALETTE_MALFORMED`
- `VERY_LOW_CHROMA`
- `DIMENSIONS_MISSING`
- `PHYSICAL_IMAGE_ASPECT_MISMATCH`
- `NON_2D_OBJECT`
- `SOURCE_LANGUAGE_MISMATCH`

Flags describe observations; they should not automatically exclude records unless a named downstream profile says so.

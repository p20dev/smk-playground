# ArtArt visual features v1

Milestone 3 produces deterministic, corpus-independent raw features for every member of the frozen
`smk-public-visual-v1` corpus.

## Version and provenance

- feature schema: `artart-visual-features`
- schema version: `1.0.0`
- extractor version: `1.0.0`
- colour implementation: `internal-oklab-published-matrices-v1`
- source corpus: `smk-public-visual-v1`

Both Parquet outputs embed the canonical/corpus SHA-256 values and a reproducible generation
timestamp anchored to the source manifest. Calculations and storage use float64.

## Palette policy

The palette source is canonical SMK bulk `colors`. No documented weights exist, so every analytical
colour has uniform weight `1/n`. Source ordering is preserved but is not interpreted as dominance.
Exact repeated hex values are deduplicated case-insensitively for analysis while source palette,
source rank and source size remain available. Repetition is never treated as weight.

`KKS8001` demonstrates the rule: five source entries become two analytical colours and receive
`PALETTE_DUPLICATE_SOURCE_COLOR`. It is outside the corpus because its image bundle is incomplete,
so the flag appears in the QA example rather than the corpus feature table.

There is deliberately no `dominant_color_weight` in v1. Normalized palette entropy is 0 for a
one-colour palette and 1 for every multi-colour palette under uniform weights. Effective palette
size consequently equals analytical palette size. Both definitions remain generic so documented
weights can replace uniform weights later, but neither should be overinterpreted in v1.

## Colour conversion and features

Each `#RRGGBB` value follows:

```text
sRGB -> linear RGB -> OKLab -> OKLCH
```

The implementation uses the published OKLab matrices. Hue is null when OKLCH chroma is below
`1e-7`; neutral colours never receive an invented hue of zero.

Centroids are weighted means in OKLab and only then converted to OKLCH. Additional compact features
are normalized entropy, effective palette size, weighted OKLab mean distance from centroid,
weighted lightness/chroma standard deviation and chroma-weighted circular hue concentration.

## Geometry

Net width/height, area, aspect ratio and natural logs exist only for finite positive, unambiguous
canonical Netto dimensions. Gross, sheet, plate, mount and pixels never substitute for missing
physical geometry. Pixel width/height and image aspect are separate digital fields.

Aspect mismatch is:

```text
abs(log(net_aspect_ratio / image_aspect_ratio))
```

Its observed median is 0.0126, P95 0.261 and P99 0.654. The conservative diagnostic threshold is
`ln(2) = 0.693147...`, meaning more than a factor-two aspect discrepancy; 19 artworks are flagged.
The flag does not change corpus membership.

## Corpus diagnostics

| Measure | Count |
|---|---:|
| Feature rows | 27,254 |
| Analytical palette rows | 113,332 |
| Achromatic palette-colour rows | 63,206 |
| Centroid hue null | 5,766 |
| Hue concentration null | 5,766 |
| Valid Netto width × height | 2,189 |
| Physical geometry missing | 25,065 |
| Aspect mismatch flagged | 19 |

Selected distributions:

| Feature | Min | Median | P95 | P99 | Max |
|---|---:|---:|---:|---:|---:|
| centroid L | 0.1771 | 0.7207 | 0.9571 | 0.9892 | 1.0000 |
| centroid chroma | ~0 | 0.0181 | 0.0746 | 0.0976 | 0.1468 |
| OKLab palette spread | 0 | 0.1685 | 0.2943 | 0.3689 | 0.5000 |
| hue concentration | 0.0279 | 0.9833 | 1.0000 | 1.0000 | 1.0000 |
| net area cm² | 5.46 | 3,897.25 | 32,823 | 70,917 | 626,990 |

Source visual nulls are brightness 62, contrast 62, saturation 871, entropy 1 and colortemp 1.
Finite colortemp remains unmodified (range -1.2760 to 15.7201 in the corpus); 143 canonical extreme
flags are carried through. Nonfinite source values were already canonical null and none enter this
corpus.

## Proposed future machine vector

The unfrozen raw candidate is:

- colour: centroid L/a/b, OKLab spread, lightness stddev, chroma stddev, hue concentration;
- SMK visual: brightness, contrast, saturation, entropy;
- optional geometry: log net width, log net height, log net area, net aspect ratio.

Do not include centroid hue alongside a/b, colortemp, raw pixel dimensions or palette entropy as an
important independent v1 signal. A future similarity layer should compare only shared available
components and renormalize configured feature weights; it must not impute stored nulls. No vector
normalization or similarity weighting is implemented here.


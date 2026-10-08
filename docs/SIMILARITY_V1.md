# Similarity v1

Milestone 5 defines three deterministic exact-distance profiles over the frozen 27,254-entity
corpus. Lower distance means more similar. Distances are not percentages or scientific certainty,
and every result exposes its active components and contribution sum.

## Shared rules

- Exact full-corpus search; no ANN index or precomputed distance matrix.
- Each component distance is divided by its deterministic sampled-pair P95 and clipped to `[0,1]`.
- Total distance is the weighted mean of active component distances.
- A missing required feature makes an entity ineligible for that profile.
- A missing optional feature omits that component and symmetrically renormalizes remaining weights;
  no value is imputed.
- Ties sort by total distance and then `smk_entity_id`, both ascending.
- Results preserve canonical entity ID, non-unique object number and quality flags.

The profile JSON binds the feature/normalized/profile input hashes, seed `20261008`, 500,000
distinct calibration pairs, exact P95 scales, transforms, weights and output semantics.

## `color-similarity-v1`

| Component | Weight | Input |
|---|---:|---|
| centroid OKLab | 0.65 | raw Euclidean L/a/b |
| palette spread | 0.20 | robust-01 absolute difference |
| chroma standard deviation | 0.10 | robust-01 absolute difference |
| hue concentration | 0.05 | natural `[0,1]` absolute difference; optional |

Centroid color is deliberately dominant. Raw OKLab geometry is preserved. Lightness standard
deviation is excluded because its corpus correlation with palette spread is approximately 0.99.
Achromatic works remain eligible because hue concentration is optional.

## `visual-character-similarity-v1`

| Component | Weight |
|---|---:|
| centroid OKLab | 0.45 |
| palette spread | 0.12 |
| chroma standard deviation | 0.08 |
| hue concentration (optional) | 0.03 |
| SMK brightness (optional) | 0.10 |
| SMK contrast (optional) | 0.05 |
| SMK saturation (optional) | 0.10 |
| SMK entropy (optional) | 0.07 |

Contrast receives modest weight because it overlaps palette spread/lightness variation. Brightness,
saturation and entropy receive more room because Milestone 4 showed only moderate overlap with the
palette-derived features. Non-centroid inputs use their stored robust/natural 0–1 values.

## `geometry-similarity-v1`

| Component | Weight |
|---|---:|
| log width | 0.20 |
| log height | 0.20 |
| log area | 0.35 |
| log aspect ratio | 0.25 |

All four normalized log-geometry inputs are required. Exactly 2,189 entities are eligible. This
specialist profile is not mixed into color or visual character.

## Pair calibration

| Component | Median | P95 | Sample n |
|---|---:|---:|---:|
| centroid OKLab | 0.153 | 0.409 | 500,000 |
| palette spread | 0.238 | 0.659 | 500,000 |
| chroma variation | 0.268 | 0.717 | 500,000 |
| hue concentration | 0.041 | 0.302 | 311,204 |
| brightness | 0.171 | 0.666 | 497,724 |
| contrast | 0.219 | 0.624 | 497,724 |
| saturation | 0.152 | 0.591 | 468,485 |
| entropy | 0.062 | 0.582 | 499,974 |

Geometry received 3,195 jointly eligible sampled pairs; component P95 values range from 0.519 to
0.552. Full quantiles are stored in the profile and summary report.

## Eligibility, stability, and performance

- color: 27,254 entities;
- visual character: 27,254 entities, using shared available optional dimensions;
- geometry: 2,189 entities.

For the deterministic QA set, each component weight was independently varied to 85% and 115% of
its frozen value. Median top-10 overlap is 10/10 and the minimum is 8/10, indicating no radical
ranking brittleness under these modest perturbations.

On the recorded local run, normalized Parquet loading took about 0.35 seconds and engine loading
including localized titles about 1.05 seconds. Exact calculation and ranking timings are recorded
separately in `similarity-summary-v1.json`. These measurements do not justify ANN.

## Interface

```text
smk similar KMS8892 --profile color --limit 10
smk similar --id 1170000000_object --profile visual --limit 10
```

Ambiguous object numbers produce an error and list canonical IDs; they are never silently
collapsed. `--include-self` is available for debugging and yields distance zero.


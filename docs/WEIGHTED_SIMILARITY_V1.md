# Weighted color similarity v1

`weighted-color-similarity-v1` is additive. It does not modify `color-similarity-v1`.

## Palette transport

For weighted palettes A and B, the transport component minimizes:

```text
sum(i,j) flow(i,j) * EuclideanOKLab(colorA_i, colorB_j)
```

subject to every source color shipping its full weight and every target color receiving its full
weight. The implementation uses deterministic exact min-cost flow on the tiny complete bipartite
palette graph. It is symmetric, order-independent and zero for identical weighted palettes.

## Profile components

The frozen profile prioritizes palette transport and weighted centroid, with smaller spread,
chroma-variation, hue-concentration and dominant-weight modifiers. Each raw component is divided
by its P95 from a fixed 10,000-pair eligible sample and clipped to `[0,1]`. Optional achromatic hue
is omitted symmetrically and active weights are renormalized.

The exact weights, scales, input hashes and calibration distributions live in
`similarity-profiles-v2.json`. Search is exact across every weighted-eligible entity; no ANN or
two-stage candidate heuristic is used unless later measurement justifies it.

```text
smk similar KMS8892 --profile weighted-color --limit 10
```

The final KMS8892 palette, neighbors, comparison with bulk color v1 and measured query performance
are stored in `weighted-similarity-summary-v1.json`.

## Frozen profile and calibration

| Component | Weight | P95 scale |
|---|---:|---:|
| weighted centroid OKLab | 0.30 | 0.5000 |
| palette transport OKLab | 0.40 | 0.5092 |
| weighted palette spread | 0.12 | 0.6770 |
| weighted chroma variation | 0.08 | 0.7015 |
| weighted hue concentration | 0.05 | 0.2470 |
| dominant-weight difference | 0.05 | 0.8083 |

Transport distance over 10,000 deterministic pairs has median 0.1738, P90 0.3968, P95 0.5092 and
P99 0.6614. Exact full-corpus KMS8892 search takes about 12.3 seconds locally. A scalar prefilter is
not adopted: only five weighted top-10 results occur in the bulk color top 200, six in the top 500
or 1,000, and one has bulk rank 6,295. Candidate reranking would therefore miss genuine weighted
neighbors.

## KMS8892

The enrichment palette contains 500 tokens:

| Color | Tokens | Weight |
|---|---:|---:|
| `#908d41` | 120 | 0.240 |
| `#fff1dc` | 103 | 0.206 |
| `#aed7ea` | 94 | 0.188 |
| `#ceeae5` | 89 | 0.178 |
| `#b7ac3e` | 33 | 0.066 |
| `#888888` | 31 | 0.062 |
| `#795025` | 26 | 0.052 |

Weighted centroid OKLab is `(0.7914, -0.0176, 0.0340)`. Dominant color is `#908d41`; entropy is
1.8014, effective palette size 6.0579, spread 0.1549 and hue concentration 0.6577.

Its weighted top 10 are KMS5549, KMS1851, KKS11245/58, KKS5936d, KKS16225a, KKSgb18373,
KKSgb8443, KKSgb7517, KKSgb13592 and KMS4209, with distances 0.1060–0.1274. Overlap with the bulk
color-v1 top 10 is zero. The ranking change follows the newly informative token-frequency mass and
palette transport, rather than a changed corpus or overwritten v1 feature.


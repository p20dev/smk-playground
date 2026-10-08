# Normalization v1

Milestone 4 freezes normalization profile `smk-public-visual-v1`, version `1.0.0`, over all
27,254 rows in `artwork-visual-features-v1.parquet`. The profile records the input SHA-256,
feature/extractor versions, generation timestamp, exact rules and per-feature corpus statistics.
Nulls remain null; no value is imputed.

## Rules

- Corpus quantiles use linear interpolation over finite, non-null values.
- `robust_01 = clamp((x - P01) / (P99 - P01), 0, 1)`. Values below/above the cutoffs are
  clipped. A P01=P99 feature returns null and is marked non-informative.
- Natural `[0,1]` semantics are retained for hue concentration and palette entropy instead of
  stretching their corpus ranges.
- Empirical percentile uses deterministic midranks: tied ranks are averaged and divided by
  `n-1`; a singleton receives 0.5.
- `robust_z = (x - median) / (1.4826 * MAD)`, without clipping. MAD=0 returns null.
- Positive physical and image ratios also receive `ln(width/height)`, where square is zero,
  landscape positive and portrait negative.
- Hue is circular. Valid centroid hue receives cosine/sine fields; null hue produces nulls.
  These fields are diagnostic and are not added to `color_core_v1`, because OKLab a/b already
  encode hue direction.

Raw OKLab L/a/b remain the canonical perceptual coordinates. Their normalized variants are useful
for generic plots, but Euclidean distance between those variants is not OKLab distance.

## Coverage and distributions

| Feature family | Complete rows |
|---|---:|
| `color_core_v1` | 21,488 |
| `visual_character_v1` | 26,383 |
| `geometry_v1` | 2,189 |
| all three | 1,801 |

Color-core incompleteness is entirely the 5,766 null hue-concentration values for achromatic
palettes. Visual-character incompleteness follows the 871 missing saturation values (including 62
rows also missing brightness/contrast). Geometry remains optional: 25,065 rows lack a complete
Netto width/height pair, and the corpus is not reduced for that reason.

Selected distribution findings:

- centroid L has median 0.7207 and P01/P99 0.3496/0.9900;
- palette spread has median 0.1685 and P01/P99 0/0.3689;
- log area has median 8.2680 and P01/P99 3.8960/11.1684 among 2,189 valid rows;
- `smk_colortemp` retains every finite extreme (range -1.2760 to 15.7201), but is excluded from
  primary vectors because of its extremes and uncertain semantics;
- each ordinary robust scaling clips approximately the bottom and top one percent of finite
  observations; exact counts are stored per feature in the profile/statistics table.

Palette entropy has MAD zero and therefore no robust z-score. Under uniform Milestone 3 weights,
entropy is overwhelmingly 1 for multi-colour palettes, while effective palette size primarily
restates analytical palette size. Neither belongs to the v1 primary machine families.

## Correlations

Correlations use pairwise complete observations and report sample count plus Pearson and Spearman.
No feature is removed automatically. The only pair above the diagnostic absolute 0.90 threshold is
palette spread versus lightness standard deviation (Pearson 0.99, Spearman 0.99; n=27,254).
SMK contrast also tracks lightness standard deviation (0.83/0.82) and palette spread (0.80/0.79).
Brightness and centroid L are related but not interchangeable (0.67/0.67); saturation and centroid
chroma similarly correlate only moderately (0.64/0.61). These results indicate that the SMK fields
partly overlap the palette-derived measures while retaining additional information.

## Deterministic examples

Representative rows are stored in `normalization-summary.json`. Selected values are shown as
raw → robust 0–1 → percentile → robust z:

| Artwork | Feature | Values |
|---|---|---|
| KMS8892 | centroid L | 0.7418 → 0.6124 → 0.5571 → 0.1381 |
| KMS8892 | palette spread | 0.1654 → 0.4483 → 0.4825 → -0.0383 |

KMS8892's raw centroid is `(0.7418, -0.0118, 0.0406)`, palette spread is 0.1654 and hue
concentration is 0.7040. Its SMK brightness/contrast/saturation/entropy values are
7.1344/2.9756/2.0800/9.6865. Netto geometry is 78 × 51.5 cm (4,017 cm²), and log aspect ratio is
0.4151. These remain features and normalized diagnostics only; they are not notes, similarity
scores or final weights.

## Artifacts

- `data/processed/normalization-profile-v1.json`
- `data/processed/artwork-normalized-features-v1.parquet`
- `data/processed/artwork-feature-vectors-v1.parquet`
- `data/reports/normalization-statistics.parquet`
- `data/reports/normalization-summary.json`


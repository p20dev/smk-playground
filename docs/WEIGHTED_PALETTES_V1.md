# Weighted enrichment palettes v1

The weighted palette source is `colorextractor.data.colors_palette_weighted_s` from separately
cached SMK enrichment responses. It is not present in the bulk snapshots and does not replace the
uniform bulk palette v1.

Observed values are whitespace-separated `#RRGGBB` tokens with repeated colors. Parsing is:

1. tokenize non-whitespace values;
2. validate complete hex tokens and normalize case;
3. retain first-occurrence order;
4. count each color;
5. assign `weight = token_count / valid_token_count`.

Invalid tokens and partial/missing values are flagged rather than silently discarded. The source
record, raw field fingerprint, token count, unique-color count, component and `_version_` remain
traceable through the cache and enrichment manifest.

`artwork-weighted-palettes-v1.parquet` uses palette source `smk_enrichment`, schema `1.0.0` and
weighting `enrichment_token_frequency`. Every entity palette sums to one within tolerance and
stores sRGB, OKLab and OKLCH coordinates.

`artwork-visual-features-v2.parquet` retains one row for every base-corpus entity. Availability is
represented by `has_weighted_palette_v1` and `weighted_palette_status`; it does not change corpus
membership. Weighted rows recompute centroid, variation, spread, Shannon entropy, normalized
entropy, effective palette size, hue concentration, dominant color and dominant weight. Explicit
lineage distinguishes them from uniform bulk features v1.

Final coverage/distributions and bulk-versus-enrichment comparison are recorded in
`enrichment-summary-v1.json` after the frozen cache build.

## Frozen-corpus findings

All 27,238 unique object-number responses succeeded and contained a valid token palette, covering
all 27,254 entities. Token counts range from 437 to 506 (median 499); unique colors range from 1 to
15 (median 4, P95 7). No palette has one token per color. There are 2,420 single-color palettes and
3,906 entities with dominant weight at least 0.9, so strongly concentrated palettes are real but
not universal.

Compared with bulk palette color sets, 27,243 entities match exactly, nine partially overlap and
two have no overlap. Six differ in palette size and 12 differ in order. This supports shared color
extraction lineage for nearly all records while still requiring separate provenance.

Dominant weight has median 0.50. Weighted entropy has median 1.08 and effective palette size median
2.96. Weighted palette spread has median 0.10. Median v1→v2 centroid shift is 0.08 OKLab (P95 0.26,
maximum 0.59), demonstrating that token-frequency weights materially change color summaries.

Every observed component `_version_` is record-specific in this snapshot (the distinct count per
component equals its record count). It behaves as a per-document update/version token, not a small
algorithm-version vocabulary suitable for distribution grouping. Component type and exact token
are therefore retained per record; no incompatible version buckets were silently merged.


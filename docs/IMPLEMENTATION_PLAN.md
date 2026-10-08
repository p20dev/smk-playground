# Implementation Plan

## Milestone 0 — Source reconnaissance + repository foundation

- verify Python package/CLI setup
- detect both expected source files:
  - `data/raw/smk_all_da.json`
  - `data/raw/smk_all_en.json`
- inspect actual top-level JSON structures without guessing
- compute bytes + SHA-256
- count/summarize records with bounded memory
- compare DA/EN identity sets
- write `source-manifest.json`
- document any structural surprises

Done when we understand the actual dumps well enough to implement the parser from evidence rather than assumptions.

## Milestone 1 — Streaming source loading + canonical schema

- implement bounded-memory loader for actual observed structure
- join DA/EN by `object_number`, never by row position
- preserve localized text where useful
- map stable non-language fields into canonical columns
- preserve source provenance/disagreements
- parse physical dimensions/units defensively

Done when a representative fixture/sample becomes deterministic canonical rows.

Status: source loading and pre-canonical audits complete. Stable source-row identity, lossless
logical Parquet, duplicate taxonomy, dimension vocabulary, palette/visual quality and DA/EN
precedence recommendations are documented. Canonical entities are implemented in Milestone 2
without collapsing duplicate `object_number` groups.

## Milestone 2 — Canonical entities + first analyzable corpus

- pair language rows only by SMK `id`
- preserve `object_number` as non-unique grouping metadata
- canonicalize fields with explicit provenance and conflicts
- resolve image bundles atomically
- preserve and normalize dimension observations without choosing conflicts
- freeze `smk-public-visual-v1` with machine-readable exclusion reasons

Status: complete. See `CANONICALIZATION.md` and `CORPUS_V1.md`. Visual/colour feature extraction
has not started.

## Milestone 3 — Weighted palette + colour conversion

- locate ordinary/weighted palette fields in the actual snapshot/enrichment data
- parse `colors_palette_weighted_s` when present
- normalize explicit weights
- implement/verify sRGB -> OKLab -> OKLCH
- preserve malformed input as quality warnings rather than crashing the run

Done when known palette fixtures produce stable colour rows and valid weights.

## Milestone 4 — Feature extraction

Implement:

- perceptual centroid
- palette entropy
- effective palette size
- palette spread
- weighted lightness/chroma variation
- hue concentration
- SMK visual fields + provenance
- physical/image geometry + logs

Done when one artwork can produce a complete feature record independently of the corpus.

## Milestone 5 — Quality layer

Implement documented flags and source/language/aspect checks.

Produce `quality-report.json` with:

- DA/EN raw record counts
- unique IDs and language overlap
- public-domain count
- usable-image/visual count
- valid feature count
- null counts by feature
- flag counts
- parser warnings/errors
- palette-size distribution
- obvious extreme values

## Milestone 6 — Pilot build

Run 100–500 representative artworks.

Review distributions and manually inspect selected records. Fix parser/source/math errors only; do not artistically tune features.

## Milestone 7 — Corpus-relative normalization

Use the frozen `smk-public-visual-v1` entity membership from Milestone 2. Do not redefine corpus
membership from an expected count.

- reference included/excluded counts and reasons from the frozen corpus artifact
- compute count/null/min/max/quantiles
- median + MAD
- implement `robust_01`
- implement `percentile_01`
- implement robust z-score
- freeze profile with source-manifest reference

## Milestone 8 — Full dataset build

Run the complete local source snapshots.

Definition of done:

Every canonical artwork has valid applicable features or explicit nulls/flags explaining missing/invalid prerequisites. Every normalization result references a frozen profile and exact source manifest.

## Milestone 9 — Similarity

Implement separate profiles rather than one magic similarity score:

- `color`
- `visual`
- `composition`

Use fast feature-vector candidate retrieval followed optionally by weighted-palette optimal-transport reranking. Do not precompute all pairs.

## Milestone 10 — Art Tone v1

Implement versioned, explainable sonification mapping separate from objective features.

Initial mapping:

- centroid hue -> chromatic pitch class
- physical area percentile -> register
- chroma -> velocity/richness
- lightness -> timbral brightness
- palette entropy -> complexity
- contrast -> attack
- hue concentration -> tonal purity

Emit exact inputs alongside every mapped result.

## Milestone 11 — Exploration

Only after Dataset v1 is trustworthy, start experimental interfaces/notebooks/apps:

- nearest-neighbour browser
- colour-space explorer
- timelines
- artist palette fingerprints
- mosaics
- sonification player

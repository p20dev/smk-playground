# AGENTS.md — SMK Playground

## Mission

Build a small, reproducible analysis pipeline for visual and colour features in Statens Museum for Kunst (SMK) artwork data. The first deliverable is **not** a web application. It is a trustworthy, reusable analytical dataset that can support later colour search, similarity, clustering, timelines, mosaics, experimental interfaces and data sonification.

Keep the project easy to understand, quick to run and cheap to develop. Prefer explicit data code over frameworks, services and premature abstraction.

## Read first

Before coding, read:

- `README.md`
- `docs/SOURCE_DATA.md`
- `docs/DATA_MODEL.md`
- `docs/FEATURE_SPEC_V1.md`
- `docs/PIPELINE.md`
- `docs/IMPLEMENTATION_PLAN.md`

The two real source snapshots already exist locally:

```text
data/raw/smk_all_da.json
data/raw/smk_all_en.json
```

They are large (~900 MB each) and intentionally ignored by Git.

## Core architecture

Treat the project as four analytical layers:

1. `source` — untouched SMK snapshot/API/enrichment input + provenance.
2. `canonical` — cleaned, language-aware values with stable field names.
3. `features` — deterministic per-artwork derived features. These MUST NOT depend on other artworks.
4. `normalized` — corpus-relative values based on a named, versioned normalization profile.

Never overwrite source data. Never silently invent missing values.

## Primary bulk source

v1 bulk ingestion uses the local JSON snapshots, not tens of thousands of API calls.

Expected paths:

- Danish: `data/raw/smk_all_da.json`
- English: `data/raw/smk_all_en.json`

Use the live SMK API/enrichment API for verification, source understanding, spot checks and future refresh utilities.

SMK documents its API as JSON/REST and states that the downloadable full JSON dataset is updated nightly. Therefore local files are immutable time-specific snapshots and MUST be fingerprinted for reproducibility.

Relevant public endpoints include:

- `https://api.smk.dk/api/v1/art?object_number=<OBJECT_NUMBER>`
- `https://enrichment.api.smk.dk/api/enrichment/<OBJECT_NUMBER>`
- `https://open.smk.dk/artwork/image/<OBJECT_NUMBER>`

## First task: inspect, do not guess

Before implementing the final parser, inspect the real two files and establish:

- SHA-256 and byte size,
- top-level JSON shape,
- actual record container/envelope,
- record counts,
- identity field presence,
- duplicate/missing `object_number` cases,
- DA/EN identity-set overlap,
- representative field shapes,
- whether language-independent fields differ between DA/EN.

Do **not** assume the two files have identical row order. Join by stable identity, preferably `object_number`.

Do **not** use `json.load()` over a ~900 MB file as the default approach. Prefer bounded-memory streaming (`ijson`) and/or a one-time manifest-bound conversion to Parquet/Arrow.

## Corpus size

Do not hardcode `39,508` as a required record count. The intended public/open visual collection may currently be around that size, but the complete dump can contain other records and SMK changes over time.

Always derive and report actual counts from the source snapshot:

- raw DA/EN records,
- unique artwork identities,
- public-domain artworks,
- records with images/visual data,
- records eligible for a given downstream profile,
- exclusions/null reasons.

## Source manifest

Create `source-manifest.json` before producing authoritative derived output. Include at least filename, language, bytes, SHA-256, observed structure, record count, generation timestamp and parser/tool version.

All authoritative derived artifacts should be traceable to a source manifest.

## Technology

Preferred v1 stack:

- Python 3.12+
- `ijson` for bounded-memory JSON streaming
- `polars` for dataframe transforms
- `pyarrow` for Parquet interoperability
- `duckdb` for local analytical querying
- `numpy` for numerical work
- a small, verified colour conversion implementation or lightweight reputable colour library
- `typer` for CLI
- `pytest` for focused tests

Avoid pandas unless a dependency forces it. Avoid Spark, Airflow, Celery, Kafka, Kubernetes, microservices and other infrastructure that this corpus does not justify.

## Repository structure

```text
smk-playground/
├─ AGENTS.md
├─ README.md
├─ START_PROMPT.md
├─ pyproject.toml
├─ .gitignore
├─ .env.example
├─ docs/
│  ├─ SOURCE_DATA.md
│  ├─ DATA_MODEL.md
│  ├─ PIPELINE.md
│  ├─ FEATURE_SPEC_V1.md
│  └─ IMPLEMENTATION_PLAN.md
├─ src/smk_playground/
│  ├─ ingest/
│  ├─ canonical/
│  ├─ features/
│  ├─ normalize/
│  ├─ quality/
│  ├─ similarity/
│  └─ sonification/
├─ tests/
│  └─ fixtures/
└─ data/
   ├─ raw/
   ├─ interim/
   ├─ processed/
   └─ reports/
```

## v1 derived outputs

Aim to produce:

- `source-manifest.json`
- `artworks.parquet`
- `palette.parquet`
- `features.parquet`
- `normalization-profile.json`
- `normalized-features.parquet`
- `quality-report.json`

Parquet is the portable source of truth for derived tabular output. DuckDB may provide local views/tables for exploration.

## Danish + English merge rules

- Never join DA/EN by row position.
- Prefer `object_number` as identity.
- Preserve localized textual metadata separately where useful.
- Do not run duplicate visual feature extraction just because both language snapshots contain the same artwork.
- If language-independent values disagree, preserve provenance and report/resolve via an explicit deterministic rule.
- Missing one language must not automatically discard an otherwise valid artwork.

## Canonical artwork rules

Use stable internal field names independent of exact SMK JSON layout.

Retain at minimum when present/useful:

- `object_number`
- public-domain flag
- localized title/object type/classification fields
- source/provenance/version information
- image width/height in pixels
- physical Netto width/height/depth in centimetres
- palette/source visual fields

### Dimensions

- Prefer **Netto** dimensions over Brutto when both exist and the semantic meaning is suitable.
- Convert supported physical units to centimetres.
- Keep unknown/ambiguous dimensions null.
- Never represent missing dimensions as zero.
- `physical_area_cm2` requires meaningful width AND height.
- Digital pixel dimensions are never a substitute for physical dimensions.

## Palette rules

Preserve original SMK palette/source fields in source/interim provenance.

Canonical palette rows should include:

- `object_number`
- `rank`
- `hex`
- `weight`
- `weight_source`
- `srgb_r`, `srgb_g`, `srgb_b`
- OKLab `l`, `a`, `b`
- OKLCH `l`, `c`, `h_deg`
- palette provenance/source/version

All explicit canonical weights must be non-negative and normalized so the sum is approximately `1.0`.

### `colors_palette_weighted_s`

Treat this defensively. The observed enrichment representation can be a space-separated sequence containing repeated hex colours. Parse valid tokens, count occurrences and convert counts into relative weights. Preserve the original source representation/provenance.

If absent or malformed, record a quality flag. Never pretend equal/fallback weights are original SMK weights.

## Colour space

Use:

```text
sRGB -> linear RGB -> OKLab -> OKLCH
```

Use OKLab as the primary Cartesian perceptual calculation space.

Hue is circular. Do not average hue degrees arithmetically. Aggregate colour centroids are calculated in OKLab and converted afterward to OKLCH.

## Feature vocabulary v1

### Colour centroid

- `centroid_l`
- `centroid_a`
- `centroid_b`
- `centroid_chroma`
- `centroid_hue_deg`
- `centroid_hue_x = cos(h)`
- `centroid_hue_y = sin(h)`

### Palette distribution

- `dominant_color_weight`
- `palette_entropy_01`
- `effective_palette_size`
- `palette_spread`
- `lightness_stddev`
- `chroma_stddev`
- `hue_concentration_01`

### SMK visual features

Preserve, when available and with provenance:

- `smk_brightness`
- `smk_contrast`
- `smk_saturation`
- `smk_colortemp`
- `smk_entropy`

Do not confuse SMK image entropy with our palette entropy.

### Geometry

- `physical_width_cm`
- `physical_height_cm`
- `physical_depth_cm`
- `physical_area_cm2`
- `physical_aspect_ratio`
- `image_aspect_ratio`
- `log_width_cm`
- `log_height_cm`
- `log_area_cm2`

Only calculate logarithms for valid positive values.

## Feature formulas

### Weighted OKLab centroid

```text
L = sum(w_i * L_i)
a = sum(w_i * a_i)
b = sum(w_i * b_i)
```

### Palette entropy

```text
H = -sum(p_i * ln(p_i))
H01 = H / ln(n)
```

For `n <= 1`, `palette_entropy_01 = 0.0`.

### Effective palette size

```text
N_eff = exp(H)
```

### Palette spread

Weighted mean Euclidean OKLab distance of palette colours from their weighted OKLab centroid.

### Hue concentration

Use a chroma-aware circular resultant with contribution weight:

```text
palette_weight * chroma
```

Return null and flag achromatic/undefined hue when total chromatic weight is effectively zero.

## Normalization v1

Normalization is corpus-level and MUST be versioned independently from feature extraction.

Initial profile:

```text
smk-public-visual-v1
```

Its exact inclusion predicate and actual membership counts must be written into the normalization profile. Do not define membership by a hardcoded expected count.

For suitable scalar features calculate:

1. `robust_01`: P01 -> 0, P99 -> 1, clamp outside.
2. `percentile_01`: empirical percentile rank.
3. `z_robust`: `(x - median) / (1.4826 * MAD)`.

Do not corpus-normalize hue as an ordinary linear scalar.

The profile JSON should record per-feature valid/null counts, min/max, median, MAD, P01/P05/P25/P50/P75/P95/P99, profile version, feature schema version, source-manifest reference and generation timestamp.

## Missing data

Missing means null.

Never:

- replace missing with zero,
- silently impute medians,
- fabricate physical measurements from pixels,
- invent palette weights and present them as SMK data.

Downstream similarity code may compare only shared available dimensions and renormalize configured weights, but must not mutate stored features.

## Quality

At minimum support/report flags such as:

- `PALETTE_MISSING`
- `PALETTE_WEIGHTS_MISSING`
- `PALETTE_MALFORMED`
- `VERY_LOW_CHROMA`
- `DIMENSIONS_MISSING`
- `PHYSICAL_IMAGE_ASPECT_MISMATCH`
- `NON_2D_OBJECT`
- `SOURCE_LANGUAGE_MISMATCH`

Quality flags are observations, not automatic deletion instructions.

## Similarity

Do not invent one universal similarity score. Later support named profiles such as:

- `color`
- `visual`
- `composition`

Use fast feature-vector candidate retrieval, then optionally rerank top candidates with a weighted-palette optimal-transport/Wasserstein-style distance. Do not precompute all pairwise distances.

## Sonification

Sonification is a separate mapping layer, never an objective artwork feature.

Initial profile: `art-tone-v1`.

Tentative mapping:

- centroid hue -> chromatic pitch class
- physical area percentile -> register
- chroma -> velocity/harmonic richness
- lightness -> timbral brightness
- palette entropy -> complexity
- contrast -> attack
- hue concentration -> tonal purity

Mappings must be versioned, deterministic and explainable by recording their exact feature inputs.

## Testing philosophy

Do not over-test or repeatedly process the whole corpus while developing small changes.

Focus tests on:

- source-shape/streaming parser fixtures,
- DA/EN identity merge behavior,
- colour conversion reference values,
- weighted-palette parsing,
- feature formulas,
- invariants (`weights ~= 1`, normalized values in range),
- deterministic output,
- null/quality behavior.

Use small fixtures and targeted milestone checks. Full-corpus runs belong at milestone boundaries.

## Development workflow

Work milestone by milestone. Make coherent commits rather than a stream of trivial commits. Keep docs aligned with material implementation decisions.

Do not add a web UI/API/service stack before the analytical Dataset v1 works and has been inspected.

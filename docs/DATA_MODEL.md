# Data Model

## Layers

### 0 — Source
Untouched Danish/English SMK snapshots plus provenance. No rewriting in place.

### 1 — Canonical
Stable internal representation with consistent units, explicit nulls and language-aware textual fields.

### 2 — Features
Deterministic values derived solely from one artwork and its source/enrichment data.

### 3 — Normalized
Values calculated relative to a named, frozen corpus/profile.

## Main artifacts

### `source-manifest.json`
Identifies exact input snapshots by filename, size, SHA-256, observed JSON structure and record counts.

### `artworks.parquet`
One canonical row per SMK entity, produced by pairing DA/EN source rows with the same top-level
SMK `id`. It includes localized values, field-level provenance/conflict status, atomic image
resolution, typed dimension observations/candidates, quality flags and corpus membership.

Suggested fields include:

- `object_number`
- `public_domain`
- localized title/object-name fields when useful (`*_da`, `*_en`)
- stable classification/object type fields
- `image_width_px`, `image_height_px`, `image_aspect_ratio`
- `physical_width_cm`, `physical_height_cm`, `physical_depth_cm`
- `physical_area_cm2`, `physical_aspect_ratio`
- source/enrichment provenance
- source-presence flags such as `present_in_da`, `present_in_en`

### `palette.parquet`
One row per artwork + canonical palette colour.

Suggested fields:

- `object_number`
- `rank`
- `hex`
- `weight`
- `weight_source`
- `srgb_r`, `srgb_g`, `srgb_b`
- `oklab_l`, `oklab_a`, `oklab_b`
- `oklch_l`, `oklch_c`, `oklch_h_deg`
- palette provenance/source/version

### `features.parquet`
One row per artwork with Feature Specification v1 values and quality flags.

### `normalized-features.parquet`
One row per artwork per normalization profile/version, or a wide equivalent if simpler to query.

### `quality-report.json`
Corpus-wide counts, missingness, exclusions, warnings and distribution diagnostics.

## Identity

`object_number` is an artwork-facing identity but is not a source-row key: 305 DA and 306 EN
groups contain more than one record. SMK's top-level `id` is present and unique for every row in
each audited snapshot (202,728 DA; 203,023 EN).

Source rows therefore use:

```text
source_row_id = "smk:" + source_language + ":" + id
```

The language prefix distinguishes the DA and EN representations of the same SMK source record.
If `id` is absent in a future source, use a deterministic SHA-256 of language + stable source
content and report the fallback. Array index is never permanent identity. A duplicate
`source_row_id` is a hard ingest error.

Keep `smk_source_id`, `object_number`, language, source-file hash and logical record hash alongside
the internal ID. The canonical entity key is the language-independent top-level SMK `id`.
Repeated `object_number` values remain separate canonical entities and are represented in
`object-number-groups.parquet`; they are never collapsed implicitly.

If duplicate IDs exist, inspect them and implement an explicit deterministic policy with provenance; do not keep an arbitrary “first row”.

### Canonical identity

```text
source_row_id = smk:<language>:<SMK id>
smk_entity_id = <SMK id>
object_number = non-unique accession/business identifier
```

DA and EN rows pair only by identical `smk_entity_id`. A disagreement in `object_number` becomes
an unresolved field conflict, not a cross-ID pairing rule.

## Manifest-bound source Parquet

`source_da.parquet` and `source_en.parquet` contain one row per source row, including selected typed
columns, audit JSON columns and `source_record_json`, which preserves the complete parsed record.
This is logical JSON preservation, not original byte-layout preservation. Parquet metadata records
the source-file and source-manifest SHA-256 values.

## Null semantics

Null means unavailable/not safely derivable.

Zero is a real value and must never stand in for missing data.

## Corpus membership

Canonical ingestion and feature extraction may include records that are not eligible for `smk-public-visual-v1`.

Normalization membership is a separate, explicit decision. Store inclusion/exclusion reasons rather than deleting records merely because a downstream profile cannot use them.

`smk-public-visual-v1` is now frozen as an analyzable source corpus, not a normalization profile.
Its exact predicate and counts are documented in `CORPUS_V1.md`. Later corpus-relative feature
normalization remains independently versioned.

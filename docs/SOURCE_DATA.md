# Source Data

## Primary v1 snapshots

```text
data/raw/smk_all_da.json
data/raw/smk_all_en.json
```

Treat both files as immutable.

## Source reconnaissance comes first

Before implementing a production parser, inspect the real files and record:

- file size,
- SHA-256,
- top-level JSON type,
- whether records are a top-level array or nested under an envelope key,
- first/last representative record shape,
- record count,
- identity field availability,
- duplicate `object_number` values,
- major field presence/null rates,
- whether Danish/English snapshots contain the same identity set,
- whether non-language fields differ between snapshots.

Do not assume record order is stable or aligned between languages.

## Large-file rule

The source files are roughly 900 MB each. Prefer streaming/token-based ingestion (`ijson`) or another bounded-memory strategy. It is acceptable to convert each snapshot once into a local columnar/intermediate representation after the source manifest has been recorded.

Do not use `json.load()` on the whole file as the default implementation.

## Source manifest

Create `data/processed/source-manifest.json` containing at least:

```json
{
  "manifest_version": "1.0.0",
  "sources": [
    {
      "language": "da",
      "path": "data/raw/smk_all_da.json",
      "bytes": 0,
      "sha256": "...",
      "record_count": 0,
      "observed_top_level": "..."
    },
    {
      "language": "en",
      "path": "data/raw/smk_all_en.json",
      "bytes": 0,
      "sha256": "...",
      "record_count": 0,
      "observed_top_level": "..."
    }
  ]
}
```

Include generation timestamp and parser/tool version where useful.

## Language merge policy

Use `object_number` as the preferred artwork join key when present and valid.

Rules:

- Never merge Danish and English rows by positional index.
- Preserve language-specific textual metadata separately (`title_da`, `title_en`, etc.) when included in the canonical dataset.
- Do not duplicate language-independent image, physical or palette features simply because they occur in both snapshots.
- If language-independent fields disagree, preserve the discrepancy/provenance and choose a documented deterministic precedence rule only where a single canonical value is required.
- Missing EN must not discard an otherwise valid DA artwork, and vice versa.

## Live SMK API

The public API and enrichment API are secondary sources in v1. Use them for:

- manual/automated spot-checks of selected records,
- understanding fields not present in the bulk snapshot,
- enrichment data retrieval when it is not already represented locally,
- future incremental refresh tooling.

Do not make tens of thousands of live requests merely to recreate data already present in the snapshots.

SMK states that its full JSON dataset download is updated nightly. Therefore every local dump is a time-specific snapshot; reproducibility depends on hashing and manifesting the exact files used.

## Milestone 1 source artifacts

The bounded-memory Python ingest uses `ijson.items(stream, "item")` and writes:

- `data/interim/source_da.parquet` — 202,728 rows;
- `data/interim/source_en.parquet` — 203,023 rows.

Every row preserves the complete parsed source record plus stable row identity and manifest/file
hash provenance. Generated audit Parquets cover duplicate object numbers, dimension vocabulary and
DA/EN source disagreements. See `DUPLICATE_AUDIT.md`, `DIMENSIONS.md` and
`SOURCE_DISAGREEMENTS.md`. Palette/visual quality and rights are summarized in
`PALETTE_VISUAL_AUDIT.md` and `RIGHTS_AUDIT.md`.

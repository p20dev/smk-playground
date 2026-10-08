# SMK Playground

A small, reproducible analysis pipeline for visual and colour features in artworks from **Statens Museum for Kunst (SMK)**.

The project first established a trustworthy, versioned analytical foundation from the locally
downloaded SMK dataset. It now includes a small exploratory web application for colour search,
similarity, weighted palettes, and deterministic data sonification.

## Local source files

The project uses these two local SMK snapshots as the primary bulk source:

```text
data/raw/smk_all_da.json
data/raw/smk_all_en.json
```

They are large (~900 MB each), must stay out of Git, and must be treated as immutable source data.

The Danish and English files should be inspected before coding assumptions about their exact envelope/record layout. The pipeline joins language variants by stable artwork identity such as `object_number`; it must never rely on row order being identical between the two files.

The live SMK API remains useful for spot-checking, enrichment lookups and future refresh tooling, but v1 bulk processing starts from the local snapshots.

## Why two languages?

Visual features are language-independent, but retaining both snapshots gives us:

- reproducible source provenance,
- Danish and English text fields for future interfaces/search,
- a way to detect language-specific or structural differences rather than assuming the dumps are identical apart from text.

For v1, Danish can act as the default canonical metadata source where a single textual value is needed, while English is retained as a parallel localized value. Do not duplicate language-independent feature extraction.

## Data model

The pipeline has four analytical layers:

```text
SMK source snapshots
        ↓
canonical artwork records
        ↓
per-artwork visual features
        ↓
corpus-relative normalization
```

### Source
Untouched values plus snapshot provenance (filename, byte size, SHA-256 and observed structure).

### Canonical
Stable internal fields, normalized units and explicit nulls. Source-language values remain attributable.

### Features
Deterministic properties calculated from one artwork only: weighted palette, OKLab/OKLCH colour statistics, perceptual centroid, palette entropy/spread, dimensions and SMK-provided visual features.

### Normalized
Values calculated relative to a named, frozen corpus/profile. Per-artwork features never depend on corpus membership; normalized values explicitly do.

## Target corpus

Do **not** hardcode `39,508` as a validation constant. The local SMK dump can contain records outside the project's intended open/visual corpus and SMK's collection changes over time.

The build must report:

1. raw record count per source snapshot,
2. unique `object_number` count,
3. public-domain count,
4. records with usable image/visual data,
5. records eligible for each downstream profile,
6. explicit exclusion/null reasons.

The first normalization profile is named:

```text
smk-public-visual-v1
```

Its exact membership must be recorded when it is frozen.

## v1 outputs

The pipeline should eventually produce:

```text
source-manifest.json
artworks.parquet
palette.parquet
features.parquet
normalization-profile.json
normalized-features.parquet
quality-report.json
```

`source-manifest.json` is important: it identifies exactly which local JSON snapshots produced the outputs.

## Colour model

Canonical calculations use:

```text
sRGB -> linear RGB -> OKLab -> OKLCH
```

OKLab is used for Cartesian averaging and distance. OKLCH is retained for human-friendly lightness, chroma and hue.

SMK weighted-palette data is converted into explicit normalized weights. Hue is circular and is never averaged naïvely as degrees.

## Development philosophy

This is a modest analytical dataset, not an enterprise platform.

Use Python + streaming JSON ingestion + Polars/PyArrow + Parquet + DuckDB. Keep stages independently runnable and inspectable. Do not build a web application, API service, worker queue, PostgreSQL deployment or vector database before Dataset v1 is trustworthy.

See:

- [`AGENTS.md`](AGENTS.md)
- [`docs/SOURCE_DATA.md`](docs/SOURCE_DATA.md)
- [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md)
- [`docs/FEATURE_SPEC_V1.md`](docs/FEATURE_SPEC_V1.md)
- [`docs/PIPELINE.md`](docs/PIPELINE.md)
- [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md)

## Current status

Milestones 0–7 complete: source structure and audits are manifested, the language snapshots have
bounded-memory source Parquets, DA/EN rows are paired into stable SMK entities, and the exact
`smk-public-visual-v1` membership rule is frozen. Deterministic raw visual features and analytical
palettes now exist. Versioned corpus statistics, normalized scalar features and three unweighted
candidate feature families are materialized. Three deterministic, explainable exact-distance
profiles now support color, visual-character and specialist geometry queries; ANN is not used.
Separately cached SMK enrichment responses add weighted palettes, v2 weighted features and an
exact palette-transport similarity profile without mutating the bulk-derived v1 artifacts. A
single-service FastAPI + React application now exposes those frozen artifacts, explicit deep
weighted similarity, and deterministic browser sonification.

Audit results are documented in:

- [`docs/DUPLICATE_AUDIT.md`](docs/DUPLICATE_AUDIT.md)
- [`docs/DIMENSIONS.md`](docs/DIMENSIONS.md)
- [`docs/SOURCE_DISAGREEMENTS.md`](docs/SOURCE_DISAGREEMENTS.md)
- [`docs/PALETTE_VISUAL_AUDIT.md`](docs/PALETTE_VISUAL_AUDIT.md)
- [`docs/RIGHTS_AUDIT.md`](docs/RIGHTS_AUDIT.md)
- [`docs/CANONICALIZATION.md`](docs/CANONICALIZATION.md)
- [`docs/CORPUS_V1.md`](docs/CORPUS_V1.md)
- [`docs/FEATURE_EXTRACTION_V1.md`](docs/FEATURE_EXTRACTION_V1.md)
- [`docs/FEATURE_EXAMPLES.md`](docs/FEATURE_EXAMPLES.md)
- [`docs/NORMALIZATION_V1.md`](docs/NORMALIZATION_V1.md)
- [`docs/FEATURE_VECTOR_V1.md`](docs/FEATURE_VECTOR_V1.md)
- [`docs/SIMILARITY_V1.md`](docs/SIMILARITY_V1.md)
- [`docs/SIMILARITY_EXAMPLES.md`](docs/SIMILARITY_EXAMPLES.md)
- [`docs/ENRICHMENT_V1.md`](docs/ENRICHMENT_V1.md)
- [`docs/WEIGHTED_PALETTES_V1.md`](docs/WEIGHTED_PALETTES_V1.md)
- [`docs/WEIGHTED_SIMILARITY_V1.md`](docs/WEIGHTED_SIMILARITY_V1.md)
- [`docs/SONIFICATION_V1.md`](docs/SONIFICATION_V1.md)
- [`docs/WEB_UI_V1.md`](docs/WEB_UI_V1.md)

Run the audited ingest with:

```bash
smk milestone1
smk milestone2
smk milestone3
smk milestone4
smk milestone5
smk similar KMS8892 --profile color --limit 10
smk enrichment status
smk similar KMS8892 --profile weighted-color --limit 10
smk web-catalog
```

## Run the application

The existing Milestones 1–6 processed artifacts must be present locally. Build the compact app
catalog once after those artifacts change:

```bash
smk web-catalog
```

Then start the single application service:

```bash
cp .env.example .env
docker compose up --build
```

Open [http://localhost:8135](http://localhost:8135). The processed directory is mounted read-only;
only `data/cache/` is writable. Set `HOST_PORT` in `.env` to publish another host port.

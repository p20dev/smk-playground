# Pipeline

## Normal path

```text
smk_all_da.json + smk_all_en.json
        ↓
source reconnaissance + SHA-256 manifest
        ↓
streaming ingest
        ↓
language-aware canonical merge
        ↓
weighted palette parsing + colour conversion
        ↓
per-artwork feature extraction
        ↓
quality checks
        ↓
pilot diagnostics
        ↓
full feature build
        ↓
select/freeze normalization corpus
        ↓
normalized features
        ↓
similarity / sonification experiments
```

## Recommended CLI stages

The exact CLI can evolve, but aim for commands conceptually like:

```bash
smk inspect-source
smk ingest
smk canonicalize
smk features
smk quality
smk normalize --profile smk-public-visual-v1
smk sonify --profile art-tone-v1
smk build-all
```

Each stage should expose explicit input/output paths and be independently rerunnable.

## Stage 0 — source reconnaissance

Before writing the final record parser:

- inspect the actual DA and EN top-level structure,
- count records without fully materializing the files in RAM,
- compute SHA-256 + byte sizes,
- sample representative records,
- compare identity sets between languages,
- report duplicates/missing IDs,
- create `source-manifest.json`.

## Ingest performance rule

The source files are large. Use bounded-memory streaming where practical. A one-time conversion to Parquet/Arrow as an interim representation is encouraged if it simplifies all later stages.

Avoid repeatedly reparsing both ~900 MB JSON snapshots for every downstream command when a manifest-bound interim artifact can be reused safely.

## Pilot

Before the full normalization build, process 100–500 representative records and inspect distributions and quality flags.

Include examples that are:

- colourful / near-monochrome,
- dark / bright,
- small / large,
- missing dimensions,
- 2D / non-2D,
- odd/missing palette data,
- present in only one language snapshot if such cases exist.

The pilot checks correctness; it is not artistic tuning.

## Full build

After a successful pilot:

1. canonicalize every valid identity,
2. emit deterministic features or explicit nulls/flags,
3. report actual corpus counts instead of expecting a hardcoded number,
4. define exact membership of `smk-public-visual-v1`,
5. compute and freeze corpus statistics,
6. emit normalized features,
7. generate summary counts/distributions and exclusions.

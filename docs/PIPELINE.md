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

## Stage 1 — audited source ingest

Milestone 1 streams `$[]` with `ijson`, rejects source-ID collisions, preserves every source row in
manifest-bound Parquet and produces duplicate, dimension and language-disagreement audits. It does
not yet collapse duplicate `object_number` groups or produce canonical artwork rows.

## Stage 2 — canonical entities + corpus freeze

Pair DA/EN by identical SMK `id`, preserve non-unique object-number groups, apply field-specific
provenance/conflict rules, resolve image bundles atomically, normalize supported dimension
observations to centimetres and write `artworks.parquet`. Freeze `smk-public-visual-v1` from
explicit rights/image/colors criteria and emit membership reasons. Colour feature extraction is a
later stage.

## Stage 3 — deterministic visual features

For each frozen corpus entity, deduplicate exact source palette colours, assign explicitly uniform
analytical weights, convert sRGB to OKLab/OKLCH, calculate compact palette statistics, carry source
visual values and derive eligible geometry. Emit scalar feature and long-form palette Parquets plus
diagnostics. Do not perform corpus-relative normalization or similarity here.

## Stage 4 — versioned corpus normalization

Profile all candidate scalars over the frozen 27,254-row corpus, freeze P01/P99, median and MAD,
and emit raw plus robust-01, empirical-midrank percentile and robust-z representations. Derive log
aspect ratios and circular hue diagnostics, preserve nulls, and publish separate unweighted color,
visual-character and optional geometry families. Similarity and final weights remain later stages.

## Stage 5 — deterministic exact similarity

Calibrate component scales from a fixed 500,000-pair sample, freeze separate color,
visual-character and geometry profiles, and perform exact full-corpus ranking with explainable
contributions. Missing optional fields renormalize shared weights; required fields determine
eligibility. No ANN index, universal score or palette transport is introduced.

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

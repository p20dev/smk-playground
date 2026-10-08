# SMK enrichment source v1

Milestone 6 treats `https://enrichment.api.smk.dk/api/enrichment/<object_number>` as a separate
source. It never writes into or reinterprets the immutable DA/EN bulk snapshots.

The frozen corpus has 27,254 entities but only 27,238 unique usable object numbers. Sixteen object
numbers each identify two corpus entities. Retrieval therefore occurs once per unique object
number, while the response manifest explicitly records every corresponding `smk_entity_id`.

## Cache and provenance

Each attempt is stored under `data/raw/enrichment/<sha256(object_number)>/<timestamp>.json` with
request/response timestamps, endpoint, HTTP status or transport failure, attempt number and the
lossless parsed JSON response. `fetch-state-v1.json` is an atomic resumable checkpoint pointing to
the latest attempt. Previous timestamped responses are never overwritten.

The defaults are two workers, 0.2 seconds delay per request and conservative exponential retry.
Successful cached records are skipped under `--resume`; failures remain visible and retryable.
`--refresh` creates a new timestamped cache response. A refreshed analysis must be frozen into a
new manifest/version rather than silently replacing an already published manifest.

```text
smk enrichment status
smk enrichment fetch --resume --concurrency 2
smk enrichment fetch --limit 100
smk enrichment inspect KMS8892
```

`enrichment-source-manifest-v1.json` binds selected cache responses, outcomes, component metadata,
weighted-palette status and canonical-entity mappings. Missing, malformed, 404 and transport/server
outcomes remain explicit.


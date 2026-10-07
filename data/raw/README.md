# Raw SMK source snapshots

Place the locally downloaded SMK JSON snapshots here:

```text
data/raw/smk_all_da.json
data/raw/smk_all_en.json
```

These files are deliberately ignored by Git.

Rules:

- Treat them as immutable source snapshots.
- Never rewrite, normalize, pretty-print or otherwise modify them in place.
- Record file size and SHA-256 before processing.
- Derived/intermediate data belongs under `data/interim/` or `data/processed/`.
- The pipeline must inspect the real top-level JSON structure before assuming array vs object/envelope shape.
- Do not load a ~900 MB file into Python as one giant object when a streaming parser can be used.

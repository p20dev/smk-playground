# Codex start prompt

Read `AGENTS.md`, `README.md` and every file under `docs/` before changing code.

The two real SMK source snapshots are already present locally:

```text
data/raw/smk_all_da.json
data/raw/smk_all_en.json
```

Start with **Milestone 0 only**. Do not jump directly into a guessed parser or full feature build.

Your first job is source reconnaissance:

1. verify both files exist,
2. compute file byte sizes and SHA-256 hashes,
3. inspect their actual top-level JSON/envelope structure using bounded-memory techniques,
4. determine how artwork records are reached,
5. count/summarize records without loading an entire ~900 MB file into one Python object,
6. inspect representative DA/EN records,
7. compare identity sets using `object_number` (including duplicates/missing IDs and DA-only/EN-only cases),
8. identify where the fields relevant to Dataset v1 actually occur,
9. write `source-manifest.json` and a concise source-reconnaissance report.

Important constraints:

- Treat `data/raw/` as immutable. Never rewrite the source JSON files.
- Do not use live API calls to rebuild information already present locally.
- Live SMK API/enrichment calls are acceptable for a few explicit verification spot-checks only.
- Do not assume DA and EN files have the same row order or identical non-language fields.
- Do not hardcode `39,508` as an expected count. Report actual counts and later define corpus membership explicitly.
- Prefer streaming (`ijson`) / bounded-memory inspection; avoid `json.load()` on the entire source dump.
- Keep the solution small. No web UI, API server, PostgreSQL, job queue or distributed infrastructure.
- Add only focused tests. Do not repeatedly run expensive full-file/full-corpus operations while making small edits.
- Make a coherent Milestone 0 commit when the source structure is understood and documented.

STOP after Milestone 0 and report:

1. exact structure of both files,
2. record/identity counts and DA/EN overlap,
3. important field locations and discrepancies,
4. source-manifest path,
5. any ambiguities that affect Milestones 1–3,
6. the concrete parser/canonicalization approach you recommend next.

Do not implement Milestones 1–3 until the actual source structure has been established from the files.

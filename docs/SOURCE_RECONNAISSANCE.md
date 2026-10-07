# Source reconnaissance — Milestone 0

Generated from the local snapshots on 2026-10-08 (Europe/Copenhagen). The raw files were
read sequentially and were not modified. The detailed machine-readable scan is written locally
to `data/reports/source-reconnaissance.json`; it is intentionally ignored as generated output.

## Files and exact structure

| Language | Bytes | SHA-256 | Records | Unique `object_number` |
|---|---:|---|---:|---:|
| DA | 910,209,972 | `8b47b7af20e0450d6a4bbc1f507edbc6f7479f28a8a100e627c6d533db8d9856` | 202,728 | 202,394 |
| EN | 860,820,598 | `b8343ee9b12034f5e0aea5ac31c3eed5d3822e576cedcbe87e8234726d34e374` | 203,023 | 202,688 |

Both files are a JSON top-level array with no envelope. Every item observed was an object, so
artwork records are reached at `$[]`. The files are not interchangeable snapshots: their row
counts and identity sets differ, and their last records differ. Row position must not be used to
join them.

The scan used `tools/source-reconnaissance.mjs` under Node.js v24.12.0. It streams 1 MiB chunks,
materializes only the current array element, and retains compact identity/fingerprint indexes.
It does not call `json.load()` or materialize either source file as one object.

## Record and identity summary

| Measure | DA | EN |
|---|---:|---:|
| Raw records | 202,728 | 203,023 |
| Unique nonblank `object_number` | 202,394 | 202,688 |
| Missing/blank `object_number` | 0 | 0 |
| IDs occurring more than once | 305 | 306 |
| Extra rows beyond one per ID | 334 | 335 |
| `public_domain == true` | 152,216 | 152,511 |
| `has_image == true` | 54,423 | 54,426 |
| Non-empty `dimensions` | 199,141 | 199,442 |
| Non-empty `colors` | 52,249 | 52,249 |
| All five SMK visual fields present | 45,024 | 45,024 |

The unique-ID union contains 202,689 identities:

- 202,393 occur in both snapshots;
- 1 is DA-only: `KKSgb81877`;
- 295 are EN-only (the first include `KKS2026-53`, `KKS2026-54`, `KKS2026-55`,
  `KKS2026-56`, and `KKS2026-57`).

The full duplicate and language-only lists are in the local machine report. Duplicate IDs must
be resolved explicitly from record provenance in Milestone 1; selecting the first row silently
would be arbitrary.

## Dataset v1 field locations

All paths below are relative to one `$[]` record.

| Dataset concern | Observed source path/shape | DA presence | EN presence | Notes |
|---|---|---:|---:|---|
| Identity | `object_number: string` | 202,728 | 203,023 | Present and nonblank in every row, but not unique. |
| Public domain | `public_domain: boolean` | 202,728 | 203,023 | Values agree on all overlapping unique IDs in the selected-field comparison. |
| Titles | `titles[].title`, plus `type` and often `language` | 202,724 arrays | 203,015 arrays | The EN snapshot is not guaranteed to contain English titles; the first EN record still has a Danish title/language tag. |
| Object type/name | `object_names[].name` | 202,699 arrays | 202,933 arrays | Localized (`Grafik` vs `Print` in the first record). |
| Physical dimensions | `dimensions[].{part,type,unit,value}` | 199,141 arrays | 199,442 arrays | Values are strings; labels/units are localized (`højde`/`millimeter` vs `height`/`mm`). Select meaningful parts such as Netto only after vocabulary inspection. |
| Image geometry | `image_width`, `image_height` | 54,272 each | 54,275 each | Numeric pixels; not physical dimensions. |
| Image availability | `has_image` | every row | every row | Seven overlapping IDs disagree between snapshots. |
| Unweighted palette | `colors: array<string>` | 52,249 | 52,249 | Selected-field fingerprints agree across overlap. |
| Suggested background | `suggested_bg_color: array<string>` | 52,248 | 52,248 | Selected-field fingerprints agree across overlap. |
| SMK visual values | top-level `brightness`, `contrast`, `saturation`, `colortemp`, `entropy` | see below | see below | `colortemp` has mixed numeric/string types. |

Visual-field presence is identical between languages: `brightness` 52,171, `contrast` 52,171,
`saturation` 45,024, `colortemp` 52,249, and `entropy` 52,249. `colortemp` is numeric in
52,237 records and a string in 12 records in each file. No field whose name contains `palette`
was observed at any depth. In particular, `colors_palette_weighted_s` is absent from both bulk
snapshots; Milestone 2 cannot claim source weights from these files.

Representative record `KKS5261` demonstrates the localization boundary: identity, image
geometry, colours and visual numbers match, while dimensions use DA `højde`/`bredde` with
`millimeter` versus EN `height`/`width` with `mm`, and object names differ. Record `KKS370`
demonstrates a normal record with physical dimensions but `has_image == false` and no palette or
visual values.

## Cross-language discrepancies

For the 202,393 overlapping unique IDs, compact fingerprints of selected nominally
language-independent top-level fields found these mismatch counts:

- `rights`: 50,468; `modified`: 334;
- `image_width` and `image_height`: 15 each;
- `image_iiif_id` and `image_iiif_info`: 11 each; `image_size`: 9;
- `has_image`: 7; `image_mime_type`: 6; `image_hq`: 6;
- `image_orientation`: 8; `image_cropped`: 1; `on_display`: 2.

Selected `colors`, `suggested_bg_color`, the five visual values, `public_domain`, `id`, creation
date, acquisition date and the stable URLs had zero mismatches in this comparison. Differences
on duplicate IDs require duplicate-aware reinspection because the compact comparison retains one
fingerprint per identity; they must not be interpreted as a final canonical precedence decision.

## Ambiguities carried into Milestones 1–3

1. `object_number` is complete but non-unique. Duplicate records need comparison by source `id`,
   timestamps and content before a deterministic keep/merge/error policy can be selected.
2. The snapshots are temporally asymmetric (295 EN-only versus one DA-only identity) and some
   nominally language-independent image metadata differs. Missing one language must be retained,
   and DA precedence alone is not safe for every image field.
3. The exact physical-dimension vocabulary and choice of meaningful Netto/Brutto/part variants
   still need a bounded vocabulary profile before unit canonicalization. Values are strings and
   labels/units are localized.
4. The bulk files have no explicit weighted palette. A later enrichment input, separately
   manifested and provenance-labelled, is needed for source weights; unweighted `colors` must not
   be presented as weighted SMK data.
5. `colortemp` needs explicit validation/coercion for its 12 string-valued cases. Titles in the EN
   file cannot be treated as English merely because the file is the EN snapshot.
6. Corpus membership remains undefined. Counts above describe raw snapshots and observable field
   availability, not membership in `smk-public-visual-v1`.

## Recommended next parser/canonicalization approach

For Milestone 1, use `ijson.items(stream, "item")` against the proven `$[]` path and write a
manifest-bound interim Parquet dataset per language in batches. Preserve source row number,
source `id`, `object_number`, snapshot language and source-manifest hash. Build a duplicate audit
grouped by `object_number` before canonical merge; do not silently deduplicate.

Canonicalize DA and EN independently first, then full-outer-join by resolved `object_number`.
Keep localized fields separately and choose each language-independent field through an explicit
field-level rule that records agreement/disagreement and provenance. Profile dimension
`part`/`type`/`unit` vocabularies before mapping Netto width/height/depth to centimetres. Preserve
mixed or unknown values as null plus diagnostics. Treat top-level `colors` as an unweighted source
palette only; defer weighted palette parsing until an actual manifested weight-bearing source has
been established.

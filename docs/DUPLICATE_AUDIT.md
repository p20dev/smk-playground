# Duplicate `object_number` audit

Milestone 1 audited every duplicate group without dropping any source row. The detailed report is
`data/reports/duplicate-object-numbers.parquet` (1,280 occurrence rows, 19 columns).

## Findings

| | DA | EN |
|---|---:|---:|
| Duplicate `object_number` groups | 305 | 306 |
| Rows in duplicate groups | 639 | 641 |
| Groups of 2 rows | 297 | 298 |
| Groups of 3 rows | 7 | 7 |
| Groups of 24 rows | 1 | 1 |

No group is logically identical. Because every group differs logically, its source JSON bytes also
cannot be identical. Every occurrence has a distinct SMK `id`; these are not accidental repeated
array rows. The most common differing fields are `id` (all 1,280 rows), `created`, `titles`,
`dimensions`, `modified`, `documentation`, `inscriptions`, `production`, and production dates.

The audit classifies 605 language-specific groups as multiple SMK source records sharing an
`object_number`. Six groups have a `verso` identity and are marked as possible alternate/subrecord
cases, but the label is diagnostic rather than a merge decision. The largest group is
`KKS1974-33/1`, with 24 distinct source records in each language. Seven groups per language have
three records; all other groups have two.

Examples demonstrate that the repeated number can cover substantially different objects:

- `DEP1064/93`: distinct `id`, creation time, inscriptions, techniques and titles;
- `DEP2387`: also differs in public-domain status, rights, dimensions, object names, production and
  acquisition metadata;
- `KKS1974-33/1`: 24 records with distinct IDs, titles, dimensions and URLs.

## Handling rule

Do not deduplicate the source layer. Preserve every row under `source_row_id`. Before creating one
canonical artwork row, classify each repeated `object_number` group using IDs, titles, part/verso
relationships, related-object fields and URLs. Only collapse a group when an explicit rule proves
that the records are versions of one artwork. Otherwise assign a later canonical group identifier
or retain multiple canonical objects. A newest-`modified` or first-row rule is not safe.


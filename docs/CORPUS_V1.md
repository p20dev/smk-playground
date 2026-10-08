# Corpus: `smk-public-visual-v1`

Milestone 2 freezes the first corpus for openly reusable visual/colour analysis. Membership is
stored on every canonical entity and materialized in
`data/processed/smk-public-visual-v1.parquet`.

## Exact inclusion predicate

An entity is included only when all conditions hold:

1. canonicalization is resolved;
2. explicit canonical `public_domain == true`;
3. canonical rights semantic is `PDM` or `CC0`;
4. the atomic canonical image bundle is complete;
5. image width and height are positive (part of bundle completeness);
6. canonical `colors` is a non-empty list;
7. there is no unresolved image-bundle conflict.

The rule does **not** require physical dimensions, English metadata, visual scalar fields,
weighted palettes or enrichment data.

## Membership

| Measure | Count |
|---|---:|
| Canonical entities | 203,023 |
| Included | 27,254 |
| Excluded | 175,769 |

Exclusion reasons are non-exclusive:

| Code | Count |
|---|---:|
| `NO_USABLE_IMAGE` | 163,059 |
| `NO_COLORS` | 150,774 |
| `NOT_PUBLIC_DOMAIN` | 50,512 |
| `RIGHTS_NOT_OPEN` | 50,512 |
| `IMAGE_CONFLICT` | 3 |
| `CANONICALIZATION_UNRESOLVED` | 1 |

Milestone 1 observed about 39.5k public-domain rows with an image/public URL. Recomputed at entity
level, that broad candidate definition contains 39,508 entities. All 27,254 corpus members overlap
it. The stricter corpus is smaller because it additionally requires a complete atomic image bundle
and non-empty `colors`; it is not forced to an expected count.

## Included-data diagnostics

- 321 included entities have no normalized physical dimension;
- 25,065 lack a complete Netto width × height pair;
- 871 have partial visual fields;
- missing visual values: saturation 871, brightness 62, contrast 62, entropy 1, colortemp 1;
- 143 included entities have a colortemp quality flag.

Physical and visual missingness does not exclude a work because those properties are independent
of whether its primary image and source colours are usable.

## Shared object numbers

There are 306 `object_number` groups containing more than one canonical SMK entity; the largest
contains 24 entities. Nineteen such groups contain corpus members, representing 35 included
entities. Members remain separate entities. `data/processed/object-number-groups.parquet` provides
the relationship for later analysis/UI without destructive merging.

## Artifacts

- `data/processed/artworks.parquet` — every canonical SMK entity;
- `data/processed/smk-public-visual-v1.parquet` — included entities;
- `data/reports/corpus-membership.parquet` — decision and reason codes for every entity;
- `data/processed/object-number-groups.parquet` — non-destructive accession-number grouping;
- `data/reports/milestone2-summary.json` — machine-readable counts and rule parameters.

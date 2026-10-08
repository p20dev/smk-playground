# Canonicalization v1

Milestone 2 builds `data/processed/artworks.parquet` from the two manifest-bound source Parquets.
It produces one row per SMK entity and does not calculate OKLab, palette weights or colour-derived
features.

## Identity levels

1. **Source row** — `source_row_id = smk:<language>:<SMK id>`.
2. **SMK entity** — `smk_entity_id = <SMK id>`, without language.
3. **Artwork-facing identifier** — `object_number`, retained as a non-unique accession/business
   identifier.

DA and EN rows are paired only when their top-level SMK `id` is identical. Different SMK IDs are
never paired merely because `object_number` matches. The audited result has 203,023 entities:
202,728 paired DA+EN entities and 295 EN-only entities. No entity is DA-only.

One paired entity, `1170314109_object`, has conflicting object numbers: DA `KKSgb81877` and EN
`KKSgb82299`. Its canonical `object_number` is null and it is flagged
`CANONICALIZATION_UNRESOLVED`.

## Field rules

For source-independent scalar/list fields:

- exact DA/EN agreement → canonical value with provenance `both`;
- value in only one language → canonical value with provenance `da` or `en`;
- genuine disagreement → both originals retained, canonical value null, status `conflict` unless
  an audited field rule exists.

Localized titles, object names/classifications, artists, production data, techniques and materials
remain in separate DA/EN columns. Source row IDs, source-file hashes and manifest hashes are
retained on every entity.

## Image bundle

Image fields are resolved atomically. A complete bundle requires `has_image == true`, positive
integer width and height, a non-empty IIIF image ID, and at least one thumbnail or native/public
image URL.

Resolution order is exact matching complete bundle, one complete source against an absent or
incomplete source, then unresolved conflict if both sources have different complete bundles. No
canonical bundle mixes fields from DA and EN.

| Status | Entities |
|---|---:|
| `IMAGE_BUNDLE_OK` | 39,956 |
| `IMAGE_BUNDLE_SINGLE_SOURCE` | 8 |
| `IMAGE_BUNDLE_CONFLICT` | 3 |
| `IMAGE_BUNDLE_INCOMPLETE` | 163,056 |

The three conflicts are `KMSsp451`, `KKSbog14617c` and `KKS1984-179`. Both source bundles remain
available for inspection.

## Dimensions

Every source observation is preserved as a nested typed struct containing canonical part/type/unit,
centimetre value where supported, original language/value fields, source-row ID and mapping status.
Non-geometric weight, duration and register-tonnage observations are preserved but not converted.

Candidate slots exist for width, height, depth, diameter and length under `net`, `gross`, `sheet`,
`plate`, `mount`, `image` and `paper`. Repeated equal observations agree. Multiple distinct values
for one slot make that slot null and retain all candidates.

- 197,517 entities have at least one normalized physical dimension;
- 9,902 have canonical Netto width and 10,331 have Netto height;
- 9,897 have a complete conflict-free Netto width × height representation;
- 1,798 additionally have Netto depth;
- 227 entities have at least one dimension-slot conflict.

`has_2d_physical_geometry` means conflict-free Netto width and height. It does not claim every
entity is rectangular or a 2D artwork. `has_3d_physical_geometry` additionally requires Netto depth.

## Rights and visual data

Known rights URLs map to `PDM`, `CC0` or `SMK_RESTRICTED_POLICY`; originals remain in `rights_da`
and `rights_en`. Counts are 151,913 PDM, 598 CC0 and 50,512 restricted-policy entities.
`public_domain` remains a separately resolved explicit source field.

The 12 source `"Infinity"` colortemp strings become canonical null with
`COLORTEMP_NONFINITE_SOURCE`. Finite values are preserved without clipping. `COLORTEMP_EXTREME`
uses absolute robust z-score greater than 10, calculated with median 3.4118087 and MAD 0.1786611
over 52,237 entity values; 481 entities are flagged. This is a statistical diagnostic, not a
scientific validity claim.

Canonical rows contain deterministic sorted quality flags, including language missingness, shared
object number, dimension conflict, image status, colortemp diagnostics, partial visual fields and
unresolved canonicalization.


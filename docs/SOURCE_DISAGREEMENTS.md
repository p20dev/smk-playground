# DA/EN source disagreement audit

The detailed field-level report is `data/reports/source-disagreements.parquet`. It compares the
202,393 shared `object_number` identities while isolating 305 duplicate identity groups that first
need duplicate resolution.

## Findings

For comparable singleton records:

- `rights`: 50,425 differences, all the same localization pair: DA
  `https://www.smk.dk/section/brug-af-museets-materiale/` versus EN
  `https://www.smk.dk/en/section/use-of-smk-material/`;
- normalized dimensions: 156 differences;
- `has_image`: 7 differences;
- image width and height: 15 differences each (8 unequal, 5 missing in DA, 2 missing in EN);
- IIIF image IDs/info: 11 differences each (3 unequal, 6 missing in DA, 2 missing in EN);
- image thumbnail/native URLs: 15 differences each.

There were no comparable-singleton disagreements in `public_domain`, `colors`, brightness,
contrast, saturation, entropy or colortemp. Palette ordering therefore also agrees across the
language snapshots wherever both contain a comparable singleton record.

The image differences are not merely localization. Examples include `KKS1984-179` (2048×3072 DA
versus 5078×6618 EN with different IIIF IDs) and `KKSgb5300` (8180×5262 DA versus 999×643 EN).
The seven `has_image` disagreements go in both directions. Dimension differences include both
small numeric conflicts (`DEP977`) and measurements present in only one language.

## Source precedence recommendation

- Identity: match cross-language rows by SMK `id` where available and verify `object_number`; do
  not use array position.
- Localized text: retain DA and EN independently with their explicit source language.
- `rights`: preserve both URLs, but map this exact localized pair to one policy concept. Use
  `public_domain` plus the original rights URL for legal provenance.
- Palette and visual values: accept the shared value when equal. If a future snapshot disagrees,
  flag it rather than apply global language precedence.
- Image metadata: choose a coherent image bundle (IIIF ID, width, height and URLs) at row level.
  Prefer the bundle that is internally complete and consistent; if both differ and are complete,
  retain both and require freshness/content verification. Never mix dimensions from one bundle
  with an image ID from the other.
- Dimensions: compare localized canonical tuples, preserve both originals, and leave conflicting
  canonical values unresolved unless an explicit part-aware rule decides them.
- Missing one language: retain the available source value with provenance.


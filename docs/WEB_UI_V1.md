# Web UI v1

Milestone 7 is one FastAPI application serving both a built React/TypeScript frontend and a JSON
API. It reads existing processed artifacts without mutating them. Only weighted-similarity query
results are written, under `data/cache/weighted-similarity/`.

## User flows

- `/` searches title, artist, classification, and object number; it also offers a deterministic
  seeded random entry point and corpus coverage figures.
- `/artwork/:id` presents the image and bilingual metadata, a proportional weighted-palette strip,
  weighted feature values, user-triggered sonification, and similarity tabs.
- `/about` explains provenance, interpretation, missingness, and the distinction between source,
  derived features, and artistic mappings.

Color similarity is the default. Visual-character and geometry profiles remain separate. The
weighted-color profile is labelled as a slower, explicit deep comparison; it is never launched by
page load or tab hover. Its exact result is cached by canonical entity ID and the SHA-256 of
`similarity-profiles-v2.json`, so profile changes invalidate old cache entries.

Audio never autoplays. Play and stop controls are keyboard accessible, palette values have visible
text labels, focus indicators are explicit, and reduced-motion preferences disable decorative
motion. Missing physical geometry is shown as unavailable rather than inferred from pixels.

## API

- `GET /api/health` and `/api/stats`
- `GET /api/artworks?q=&limit=&offset=&classification=&has_physical=&chromatic=`
- `GET /api/artworks/random?seed=`
- `GET /api/resolve/{object_number}` (retains ambiguous object-number groups)
- `GET /api/artworks/{smk_entity_id}`
- `GET /api/artworks/{smk_entity_id}/similar?profile=color|visual|geometry|weighted-color`

The compact web catalog is reproducibly built with `smk web-catalog`. Application startup fails
with an explicit artifact list when required processed files are absent; it never rebuilds or
downloads analytical data automatically.

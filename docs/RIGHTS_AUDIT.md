# Rights and public-domain reconnaissance

The machine-readable profile is `data/reports/rights-public-domain-profile.json`. This audit does
not freeze `smk-public-visual-v1`.

## Rights values

| Value | DA | EN |
|---|---:|---:|
| Public Domain Mark 1.0 | 151,618 | 151,913 |
| CC0 1.0 | 598 | 598 |
| SMK use-material policy, localized URL | 50,512 | 50,512 |

The DA/EN rights disagreement is a URL-localization effect for comparable singleton records: DA
uses the Danish use-material policy URL and EN uses its English counterpart. `public_domain`
itself agrees across comparable records. Preserve the original URL but map these two URLs to one
policy concept for analysis.

## Availability combinations

| Snapshot | Public domain + image + public URL | Public domain, no image/URL | Not public domain + image + URL |
|---|---:|---:|---:|
| DA | 39,505 | 112,711 | 14,918 |
| EN | 39,506 | 113,005 | 14,920 |

There are also two non-public-domain rows per language with a public image URL while `has_image` is
false. Image and rights indicators should therefore be tested explicitly rather than inferred from
URL presence alone.

## Recommendation for the next milestone

A candidate “public visual artwork” predicate should require an explicitly public-domain rights
state (Public Domain Mark or CC0 plus `public_domain == true`), a coherent usable image bundle,
and a resolved canonical artwork identity. It should separately report object classification and
exclude/flag non-artwork or unsuitable visual classes through an explicit vocabulary, not an
assumption that every source record is a 2D artwork. The final rule and membership count remain
deliberately unfrozen until duplicate resolution and canonical artwork generation are complete.


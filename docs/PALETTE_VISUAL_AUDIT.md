# Palette and SMK visual-field audit

The machine-readable profile is `data/reports/palette-visual-profile.json`.

## `colors`

`colors` is missing or not an array in 150,479/202,728 DA records (74.23%) and
150,774/203,023 EN records (74.26%). The 52,249 arrays in each language contain 1–19 colours;
the most common lengths are five (9,463), four (9,035), three (7,447), six (7,170) and two
(6,667). All values match strict six-digit `#RRGGBB` syntax.

One record, `KKS8001`, repeats colours within its palette:
`#F4C6A3` twice and `#9B9B9B` three times. Repetition must be preserved; without source
documentation it must not be silently interpreted as weight. Comparable DA/EN singleton palettes
have zero value or ordering disagreements.

## Visual fields

Counts and distribution summaries are identical across languages for the shared visual data:

| Field | Numeric | Median | P01 | P99 | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
| brightness | 52,171 | 7.296492 | 2.311502 | 8.939394 | 0.575758 | 9.090909 |
| contrast | 52,171 | 3.461959 | 0.544415 | 7.249865 | 0.095043 | 9.672021 |
| saturation | 45,024 | 1.494608 | 0.141818 | 5.924530 | 0.000001 | 9.765914 |
| entropy | 52,249 | 9.513508 | 3.768011 | 9.792444 | 0.685058 | 9.792481 |
| colortemp | 52,237 | 3.411809 | 2.840766 | 5.679331 | -1.276565 | 2.674e27 |

The 12 textual `colortemp` values are all exactly `"Infinity"`, in both languages, affecting:

`KMS7655/12`, `KMS8868`, `KKS1995-40a/2`, `KKS1995-40a/1`, `KKS1995-40a/4`,
`KKSbog7658/4`, `KMS7739/3`, `KMS7820`, `KMS7830`, `KMS7768`, `KMS7901`, and
`KKSbog7658`.

They are malformed numeric values and remain explicit diagnostics. Numeric `colortemp` also has
serious outliers: 89 values are negative, 77 exceed 10, 19 exceed 100 and 11 exceed one million.
The largest is `KMS7561/4` at `2.6739636e27`. These values are preserved but must not be treated as
valid feature inputs without a documented validity range/source correction. No other visual field
has malformed values in the audit.


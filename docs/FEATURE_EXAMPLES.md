# Feature examples

Values below are deterministic outputs from extractor v1. OKLCH tuples are `(L, C, hue°)`; `null`
hue means chroma below `1e-7`.

## KMS8892 — required corpus example with physical dimensions

- Source/analytical palette: 7 / 7 colours, uniform weight 1/7.
- OKLCH: `#908d41` (0.6297, 0.0986, 106.85), `#fff1dc` (0.9637, 0.0315, 78.17),
  `#aed7ea` (0.8561, 0.0505, 227.77), `#ceeae5` (0.9152, 0.0302, 183.74),
  `#b7ac3e` (0.7331, 0.1295, 103.59), `#888888` (0.6268, ~0, null), and
  `#795025` (0.4679, 0.0801, 64.80).
- Centroid OKLab: (0.7418, -0.0118, 0.0406); OKLCH: (0.7418, 0.0423, 106.18°).
- Spread 0.1654; hue concentration 0.7040.
- SMK visual: brightness 7.1344, contrast 2.9756, saturation 2.0800, entropy 9.6865,
  colortemp 3.3317.
- Netto 78 × 51.5 cm; area 4,017 cm²; physical/image aspect mismatch 0.000048.
- Flags: `IMAGE_BUNDLE_OK`.

## KKS8001 — required duplicate-colour QA example, outside corpus

- Source palette: `#F4C6A3`, `#F4C6A3`, `#9B9B9B`, `#9B9B9B`, `#9B9B9B`.
- Analytical palette: `#f4c6a3` (0.8583, 0.0702, 58.91°) and `#9b9b9b`
  (0.6895, ~0, null), each with uniform analytical weight 0.5.
- Centroid OKLab: (0.7739, 0.0181, 0.0301); OKLCH: (0.7739, 0.0351, 58.91°).
- Spread 0.0914; hue concentration 1.0.
- Source visual and geometry are unavailable.
- Flags include `PALETTE_DUPLICATE_SOURCE_COLOR`, `IMAGE_BUNDLE_INCOMPLETE`,
  `VISUAL_FIELDS_PARTIAL`, and `PHYSICAL_GEOMETRY_MISSING`.
- It is not added to either corpus feature Parquet.

## KMS1571 — near-achromatic

- Palette: `#111111`, `#222222`; both have null hue.
- Centroid OKLCH: (0.2148, ~0, null).
- Spread 0.0372; hue concentration null.
- Netto 66 × 40.5 cm.
- Flags: `PALETTE_ACHROMATIC`, `CENTROID_ACHROMATIC`,
  `HUE_CONCENTRATION_UNAVAILABLE`.

## KAS782 — colourful/high-spread deterministic sample

- Palette: `#b97438`, `#b7ac3e`, `#000000`, `#33140c`, `#fcaa6b`, uniform weight 0.2.
- Chromatic hues cluster around orange/yellow (35.54°–103.59°); black has null hue.
- Centroid OKLCH: (0.4793, 0.0772, 68.93°).
- Spread 0.2953; hue concentration 0.9149.
- SMK saturation 4.7511 and brightness 3.7184.
- Physical geometry is unavailable; the image is 1080 × 1080 px.

## KKS5261 — corpus example without Netto geometry

- Palette: `#b7ac3e`, `#956830`, `#77733d`, `#ffffff`.
- Centroid OKLCH: (0.7081, 0.0714, 93.52°).
- Spread 0.1721; hue concentration 0.9618.
- Image 4,992 × 6,287 px; physical Netto geometry remains null rather than substituting sheet
  measurements or pixels.
- Flags include `PHYSICAL_GEOMETRY_MISSING`.


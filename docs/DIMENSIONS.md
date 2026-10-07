# Dimension vocabulary audit

The complete DA and EN snapshots were profiled before implementing canonical geometry. The detailed
frequency/cross-tab dataset is `data/reports/dimension-vocabulary.parquet`.

## Coverage and quality

| Measure | DA | EN |
|---|---:|---:|
| Parsed dimension entries | 430,613 | 431,230 |
| Numeric text values | 430,429 | 431,044 |
| Missing values | 184 | 186 |
| Records without a dimension array | 3,587 | 3,581 |
| Missing `part` entries | 2,715 | 2,732 |
| Missing `type` entries | 265 | 265 |
| Missing `unit` entries | 292 | 310 |
| Exact duplicate measurements beyond first | 23 | 24 |
| Conflicting values for same row/part/type/unit | 413 | 413 |

No non-empty malformed numeric text was observed: every present `value` matched the strict numeric
grammar. Missing values remain missing. Conflicts and duplicate measurements still require
row-level diagnostics during canonicalization.

## Vocabulary

The language files localize type/unit more consistently than part:

| Canonical concept | DA observed | EN observed |
|---|---|---|
| width | `bredde` (208,330) | `width` (208,636) |
| height | `højde` (209,736) | `height` (210,033) |
| depth | `dybde` (11,301) | `depth` (11,306) |
| diameter | `diameter` (913) | `diameter` (914) |
| length | `længde` (22) | `length` (31) |
| millimetres | `millimeter` (396,316), `mm` (22), typo `milimeter` (520) | `mm` (397,447) |
| centimetres | `centimeter` (33,402), `cm` (2) | `cm` (33,434) |

Non-geometric types include weight (`vægt`/`weight`, 39 each), playing time
(`spilletid`/`playing time`, 5 each), and one `bruttoregisterton`. Their units include kg/kilo,
minutes and seconds; they must not enter width × height calculations.

The largest part labels are sheet (`bladmaal`, `bladmål`, `Bladmål`), plate
(`plademaal`, `plademål`, `Plademål`), `Netto`/`netto`, mounting, image and `Brutto`/`brutto`.
Both language snapshots retain Danish part labels. Case, `aa`/`å`, and `*mål` spelling variants
are source variation rather than different physical concepts.

## Proposed explicit mapping

Canonicalization should normalize Unicode, trim, case-fold and map only listed aliases:

| Source aliases | Canonical part/axis/unit |
|---|---|
| `Netto`, `netto`, `Nettomål` | `net` part |
| `Brutto`, `brutto`, `Bruttomål`, `bruttomål` | `gross` part |
| `bladmaal`, `bladmål`, `Bladmål`, `Bladmaal` | `sheet` part |
| `plademaal`, `plademål`, `Plademål`, `Plademaal` | `plate` part |
| `monteringsmaal`, `monteringsmål` | `mount` part |
| `billedmaal`, `billedmål`, `Billedmål` | `image` part |
| `papirmål` | `paper` part |
| `bredde`, `width` | `width` |
| `højde`, `height` | `height` |
| `dybde`, `depth` | `depth` |
| `diameter` | `diameter` |
| `længde`, `length` | `length` |
| `millimeter`, `milimeter`, `mm` | `mm`, factor to cm `0.1` |
| `centimeter`, `cm` | `cm`, factor to cm `1.0` |

Prefer a complete, non-conflicting `net` width/height pair. Keep plate, sheet, image, paper and
mount dimensions separately rather than silently treating them as equivalent. Gross is a fallback
only under an explicitly named policy. Diameter is not width; depth/diameter and object classes such
as sculpture, relief, installation, statue, object, audio/video and multi-part work make generic
width × height potentially misleading. Unknown parts/types/units stay raw and canonical geometry
stays null.


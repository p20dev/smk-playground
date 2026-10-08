# Similarity examples

All statements below are deterministic feature comparisons, not aesthetic judgments.

## KMS8892

Entity: `1170009810_object`. Title: Udsigt fra en vej i udkanten af Næstved.

Query features:

`{"centroid_a": -0.011783688836877545, "centroid_b": 0.04060318013487916, "centroid_l": 0.7417738706964976, "chroma_stddev": 0.04160784030178029, "hue_concentration_01": 0.7039520108269886, "log_net_area_cm2": 8.298290634359283, "log_net_aspect_ratio": 0.4151270190199013, "log_net_height_cm": 3.9415818076696905, "log_net_width_cm": 4.356708826689592, "palette_spread_oklab": 0.16540494792170796, "smk_brightness": 7.1343875, "smk_contrast": 2.9756057, "smk_entropy": 9.686463, "smk_saturation": 2.0800343}`

### color-similarity-v1

| Rank | Object | Title | Distance | Contributions | Factual explanation |
|---:|---|---|---:|---|---|
| 1 | KKSgb12500 | Næstved | 0.045643 | centroid_oklab=0.0274, palette_spread=0.0094, chroma_stddev=0.0020, hue_concentration=0.0069 | similar centroid color |
| 2 | KKS8511j | Uglspils testamente | 0.052996 | centroid_oklab=0.0393, palette_spread=0.0050, chroma_stddev=0.0066, hue_concentration=0.0021 | similar centroid color |
| 3 | KKSgb4181 | Telemachos møder Odysseus forklædt som tigger hos hyrden Eumaios - Odysseus; fragment af hele kompositionen. | 0.057937 | centroid_oklab=0.0105, palette_spread=0.0142, chroma_stddev=0.0021, hue_concentration=0.0311 | similar centroid color |
| 4 | KKS9507 | Landskab med markvej | 0.061763 | centroid_oklab=0.0212, palette_spread=0.0075, chroma_stddev=0.0001, hue_concentration=0.0330 | similar centroid color |
| 5 | KKS2015-61 | Forskellige skitser, bl.a. farvelagt skitse til "Diogenes" | 0.061972 | centroid_oklab=0.0314, palette_spread=0.0098, chroma_stddev=0.0036, hue_concentration=0.0171 | similar centroid color |
| 6 | KKS6798 | Freia | 0.062060 | centroid_oklab=0.0100, palette_spread=0.0001, chroma_stddev=0.0024, hue_concentration=0.0495 | similar centroid color |
| 7 | KKS8009 | Profilportræt af J. F. Struense | 0.062098 | centroid_oklab=0.0078, palette_spread=0.0073, chroma_stddev=0.0012, hue_concentration=0.0457 | similar centroid color |
| 8 | KKS1975-885 | Den fejrede Pajuelera's mandige mod (i arenaen) i Saragossa | 0.062098 | centroid_oklab=0.0078, palette_spread=0.0073, chroma_stddev=0.0012, hue_concentration=0.0457 | similar centroid color |
| 9 | KKSgb8331 | Sørup Kirke, Angel | 0.062699 | centroid_oklab=0.0458, palette_spread=0.0118, chroma_stddev=0.0000, hue_concentration=0.0051 | similar centroid color |
| 10 | KKSgb7286 | "Collegium politicum" (Den politiske kandestøber) | 0.063881 | centroid_oklab=0.0191, palette_spread=0.0048, chroma_stddev=0.0004, hue_concentration=0.0396 | similar centroid color |

### visual-character-similarity-v1

| Rank | Object | Title | Distance | Contributions | Factual explanation |
|---:|---|---|---:|---|---|
| 1 | KKS1975-885 | Den fejrede Pajuelera's mandige mod (i arenaen) i Saragossa | 0.047052 | centroid_oklab=0.0054, palette_spread=0.0044, chroma_stddev=0.0010, hue_concentration=0.0274, brightness=0.0009, contrast=0.0027, saturation=0.0019, entropy=0.0034 | similar centroid color |
| 2 | KKS1640 | Aften på havet | 0.058309 | centroid_oklab=0.0117, palette_spread=0.0091, chroma_stddev=0.0032, hue_concentration=0.0187, brightness=0.0117, contrast=0.0002, saturation=0.0013, entropy=0.0025 | similar centroid color |
| 3 | KKSgb10716 | Søkamp mellem danske fartøjer og et tyrkisk sørøverskib | 0.058842 | centroid_oklab=0.0334, palette_spread=0.0015, chroma_stddev=0.0012, hue_concentration=0.0139, brightness=0.0027, contrast=0.0007, saturation=0.0053, entropy=0.0002 | similar centroid color |
| 4 | KKS8511j | Uglspils testamente | 0.061473 | centroid_oklab=0.0272, palette_spread=0.0030, chroma_stddev=0.0053, hue_concentration=0.0013, brightness=0.0112, contrast=0.0003, saturation=0.0112, entropy=0.0020 | similar centroid color |
| 5 | KKSgb14069 | En siddende kvinde vendt mod højre, i en bønligt ydmyg stilling | 0.064192 | centroid_oklab=0.0357, palette_spread=0.0006, chroma_stddev=0.0100, hue_concentration=0.0065, brightness=0.0014, contrast=0.0026, saturation=0.0029, entropy=0.0045 | similar centroid color |
| 6 | KMS1989 | Trompe l'oeil. Bagsiden af et indrammet maleri | 0.065277 | centroid_oklab=0.0078, palette_spread=0.0047, chroma_stddev=0.0049, hue_concentration=0.0297, brightness=0.0079, contrast=0.0001, saturation=0.0078, entropy=0.0023 | similar centroid color |
| 7 | KKSgb11028 | En elefant | 0.067431 | centroid_oklab=0.0349, palette_spread=0.0033, chroma_stddev=0.0116, hue_concentration=0.0028, brightness=0.0054, contrast=0.0036, saturation=0.0014, entropy=0.0044 | similar centroid color |
| 8 | KMS8825 | Åens udløb | 0.068133 | centroid_oklab=0.0248, palette_spread=0.0054, chroma_stddev=0.0087, hue_concentration=0.0138, brightness=0.0073, contrast=0.0041, saturation=0.0015, entropy=0.0025 | similar centroid color |
| 9 | KKS12774 | Molen ved Dyrnæs. Gråvejr | 0.068331 | centroid_oklab=0.0332, palette_spread=0.0114, chroma_stddev=0.0064, hue_concentration=0.0008, brightness=0.0006, contrast=0.0124, saturation=0.0030, entropy=0.0004 | similar centroid color |
| 10 | KKS8009 | Profilportræt af J. F. Struense | 0.070208 | centroid_oklab=0.0054, palette_spread=0.0044, chroma_stddev=0.0010, hue_concentration=0.0274, brightness=0.0013, contrast=0.0069, saturation=0.0224, entropy=0.0014 | similar centroid color |

### geometry-similarity-v1

| Rank | Object | Title | Distance | Contributions | Factual explanation |
|---:|---|---|---:|---|---|
| 1 | KMSsp213 | Landskab med vej forbi et rettersted | 0.002788 | log_width=0.0006, log_height=0.0000, log_area=0.0006, log_aspect=0.0016 | shared normalized feature values |
| 2 | KMSst82 | En bjerghule | 0.011366 | log_width=0.0018, log_height=0.0029, log_area=0.0043, log_aspect=0.0024 | shared normalized feature values |
| 3 | KMS1700 | Parti af bugten ved Kalkbrænderiet set fra Strandpromenaden mod nord. Stille sommereftermiddag | 0.012536 | log_width=0.0030, log_height=0.0019, log_area=0.0045, log_aspect=0.0031 | shared normalized feature values |
| 4 | KMSsp295 | Jagtstilleben med døde fugle og en jagthund | 0.013413 | log_width=0.0018, log_height=0.0019, log_area=0.0000, log_aspect=0.0096 | shared normalized feature values |
| 5 | KMS448 | Parti af Sjællands nordkyst ved Dronningmølle | 0.017326 | log_width=0.0042, log_height=0.0029, log_area=0.0065, log_aspect=0.0038 | shared normalized feature values |
| 6 | KMS4458 | Skovlandskab med Johannes Døberen i ødemarken, Johannes Døberens prædiken og Jesu dåb | 0.019421 | log_width=0.0048, log_height=0.0038, log_area=0.0079, log_aspect=0.0030 | shared normalized feature values |
| 7 | KMSsp175 | Selskab i en park (Den fortabte Søn hos skøgerne?) | 0.021563 | log_width=0.0042, log_height=0.0010, log_area=0.0031, log_aspect=0.0134 | shared normalized feature values |
| 8 | KMS7105 | Landevejen ved Mogenstrup. Efterår | 0.025227 | log_width=0.0053, log_height=0.0066, log_area=0.0109, log_aspect=0.0024 | shared normalized feature values |
| 9 | KMS7601 | Fra Den Kongelige Malerisamling på Christiansborg Slot | 0.025619 | log_width=0.0048, log_height=0.0066, log_area=0.0104, log_aspect=0.0039 | shared normalized feature values |
| 10 | KMS3040 | Nymfer i en grotte | 0.028021 | log_width=0.0012, log_height=0.0066, log_area=0.0070, log_aspect=0.0132 | shared normalized feature values |

## KMS1571

Entity: `1170013658_object`. Title: Interiør.

Query features:

`{"centroid_a": 1.7388777917570764e-11, "centroid_b": 8.006482379863122e-09, "centroid_l": 0.21480126006860106, "chroma_stddev": 1.3852316851121162e-09, "hue_concentration_01": null, "log_net_area_cm2": 7.890956716138919, "log_net_aspect_ratio": 0.488352767913932, "log_net_height_cm": 3.7013019741124933, "log_net_width_cm": 4.189654742026425, "palette_spread_oklab": 0.03716348815137517, "smk_brightness": 4.250505, "smk_contrast": 1.2342123, "smk_entropy": 9.539091, "smk_saturation": 1.3943743}`

### color-similarity-v1

| Rank | Object | Title | Distance | Contributions | Factual explanation |
|---:|---|---|---:|---|---|
| 1 | KMSsp405 | Kristus i Emmaus | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 2 | DEP7 | René Descartes (1596-1650) | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 3 | DEP697 | Roslagsgatan, Stockholm | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 4 | KMSsp289 | Stenkartouche med guirlande af frugt og blomster | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 5 | KMS3885 | En gammel kone | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 6 | KMS3986 | Fingal ser sine forfædres ånder ved månens skin | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 7 | KMS1307 | Portræt af fru Gumperd | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 8 | KMS3735 | Jagthunde og vildt | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 9 | KMS3886 | Hjemkomsten fra en fuglejagt | 0.054877 | centroid_oklab=0.0163, palette_spread=0.0044, chroma_stddev=0.0342 | similar centroid color; hue concentration unavailable |
| 10 | KMS594 | Potuanerne undres ved at se Niels Klims knæfald for den vise fyrste | 0.062067 | centroid_oklab=0.0270, palette_spread=0.0039, chroma_stddev=0.0312 | similar centroid color; hue concentration unavailable |

### visual-character-similarity-v1

| Rank | Object | Title | Distance | Contributions | Factual explanation |
|---:|---|---|---:|---|---|
| 1 | KMSsp405 | Kristus i Emmaus | 0.050142 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000, brightness=0.0401, contrast=0.0026, saturation=0.0032, entropy=0.0042 | similar centroid color; hue concentration unavailable |
| 2 | KMS3885 | En gammel kone | 0.050661 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000, brightness=0.0303, contrast=0.0087, saturation=0.0109, entropy=0.0007 | similar centroid color; hue concentration unavailable |
| 3 | DEP7 | René Descartes (1596-1650) | 0.051446 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000, brightness=0.0299, contrast=0.0023, saturation=0.0168, entropy=0.0024 | similar centroid color; hue concentration unavailable |
| 4 | KMS3986 | Fingal ser sine forfædres ånder ved månens skin | 0.060012 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000, brightness=0.0233, contrast=0.0025, saturation=0.0280, entropy=0.0063 | similar centroid color; hue concentration unavailable |
| 5 | KMS3735 | Jagthunde og vildt | 0.065779 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000, brightness=0.0248, contrast=0.0020, saturation=0.0356, entropy=0.0034 | similar centroid color; hue concentration unavailable |
| 6 | KMS1307 | Portræt af fru Gumperd | 0.075435 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000, brightness=0.0401, contrast=0.0026, saturation=0.0146, entropy=0.0181 | similar centroid color; hue concentration unavailable |
| 7 | DEP697 | Roslagsgatan, Stockholm | 0.079666 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000, brightness=0.0279, contrast=0.0044, saturation=0.0416, entropy=0.0058 | similar centroid color; hue concentration unavailable |
| 8 | KMSsp289 | Stenkartouche med guirlande af frugt og blomster | 0.079940 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000, brightness=0.0401, contrast=0.0077, saturation=0.0237, entropy=0.0085 | similar centroid color; hue concentration unavailable |
| 9 | KMS1497 | Begyndende aftenskumring i en skov. Motiv fra Iselingen | 0.085520 | centroid_oklab=0.0422, palette_spread=0.0188, chroma_stddev=0.0000, brightness=0.0142, contrast=0.0042, saturation=0.0026, entropy=0.0033 | similar centroid color; hue concentration unavailable |
| 10 | KMSsp868 | Et måneskinsstykke. Overfarten over Lillebælt ved Snoghøj | 0.087103 | centroid_oklab=0.0403, palette_spread=0.0057, chroma_stddev=0.0000, brightness=0.0135, contrast=0.0002, saturation=0.0028, entropy=0.0246 | similar centroid color; hue concentration unavailable |

### geometry-similarity-v1

| Rank | Object | Title | Distance | Contributions | Factual explanation |
|---:|---|---|---:|---|---|
| 1 | KMSsp373 | Måneskinslandskab med mytologisk (?) motiv | 0.008385 | log_width=0.0003, log_height=0.0020, log_area=0.0020, log_aspect=0.0041 | shared normalized feature values |
| 2 | KMS6072 | Stående tyr | 0.015935 | log_width=0.0038, log_height=0.0024, log_area=0.0058, log_aspect=0.0039 | shared normalized feature values |
| 3 | KMS3682 | En bro ved Sorrento | 0.016740 | log_width=0.0037, log_height=0.0000, log_area=0.0035, log_aspect=0.0096 | shared normalized feature values |
| 4 | KMS3809 | Hedestudie | 0.019840 | log_width=0.0015, log_height=0.0036, log_area=0.0019, log_aspect=0.0129 | shared normalized feature values |
| 5 | KMS7214 | Bakkedrag bag Møns Klint (Jydeleje) | 0.021231 | log_width=0.0015, log_height=0.0051, log_area=0.0059, log_aspect=0.0088 | shared normalized feature values |
| 6 | DEP297 | Dansk landskab | 0.024781 | log_width=0.0056, log_height=0.0012, log_area=0.0064, log_aspect=0.0116 | shared normalized feature values |
| 7 | KMSsp277 | Venus begræder den døde Adonis | 0.028679 | log_width=0.0067, log_height=0.0033, log_area=0.0092, log_aspect=0.0095 | shared normalized feature values |
| 8 | KMS6155 | Ruinerne af det antikke teater ved Tusculum | 0.029898 | log_width=0.0021, log_height=0.0072, log_area=0.0084, log_aspect=0.0122 | shared normalized feature values |
| 9 | KMS4167 | Et hus på Alheden | 0.031200 | log_width=0.0076, log_height=0.0083, log_area=0.0146, log_aspect=0.0007 | shared normalized feature values |
| 10 | KMS7709 | Tøbrud | 0.033416 | log_width=0.0075, log_height=0.0012, log_area=0.0082, log_aspect=0.0165 | shared normalized feature values |

## KKS10234

Entity: `1170013295_object`. Title: Kunstnerens datter båret af hendes amme.

Query features:

`{"centroid_a": 0.1292024592463376, "centroid_b": 0.06973442719350281, "centroid_l": 0.7071157211187032, "chroma_stddev": 0.0, "hue_concentration_01": 1.0, "log_net_area_cm2": null, "log_net_aspect_ratio": null, "log_net_height_cm": null, "log_net_width_cm": null, "palette_spread_oklab": 0.0, "smk_brightness": 8.002823, "smk_contrast": 1.353646, "smk_entropy": 9.792471, "smk_saturation": 4.476761}`

### color-similarity-v1

| Rank | Object | Title | Distance | Contributions | Factual explanation |
|---:|---|---|---:|---|---|
| 1 | KKSgb3856 | Jordemoderen. Studie til Pigen fra Andros. [Jordemoderen forlader Androspigens hus] | 0.076569 | centroid_oklab=0.0766, palette_spread=0.0000, chroma_stddev=0.0000, hue_concentration=0.0000 | similar centroid color |
| 2 | KKS2615 | Bagside af omslag til M. Hammerichs oversættelse af Kalidasas, "Sakuntala", København 1845 | 0.076569 | centroid_oklab=0.0766, palette_spread=0.0000, chroma_stddev=0.0000, hue_concentration=0.0000 | similar centroid color |
| 3 | KMS6604 | Udkast til en portrætgruppe. Regine Sophie Tutein, f. Wraatz med sønnen Peter | 0.076569 | centroid_oklab=0.0766, palette_spread=0.0000, chroma_stddev=0.0000, hue_concentration=0.0000 | similar centroid color |
| 4 | KKS1977-473 | Motiv fra et østgrønlandsk sagn (Et fuglevæsen med barnehoved. Den ene af Andreassen-familiens to familietupilakker) | 0.076569 | centroid_oklab=0.0766, palette_spread=0.0000, chroma_stddev=0.0000, hue_concentration=0.0000 | similar centroid color |
| 5 | KKSgb7520 | Løve, vendt mod højre, med højre forpote på en kugle | 0.076569 | centroid_oklab=0.0766, palette_spread=0.0000, chroma_stddev=0.0000, hue_concentration=0.0000 | similar centroid color |
| 6 | KKSgb7665 | Mandlig modelstudie, halvtliggende | 0.076569 | centroid_oklab=0.0766, palette_spread=0.0000, chroma_stddev=0.0000, hue_concentration=0.0000 | similar centroid color |
| 7 | KKS8072 | Middelfart | 0.076569 | centroid_oklab=0.0766, palette_spread=0.0000, chroma_stddev=0.0000, hue_concentration=0.0000 | similar centroid color |
| 8 | KKSgb6160 | Et ophængt dødt egern | 0.076569 | centroid_oklab=0.0766, palette_spread=0.0000, chroma_stddev=0.0000, hue_concentration=0.0000 | similar centroid color |
| 9 | KKS13801 | Sappho og Mytilenerinden | 0.076569 | centroid_oklab=0.0766, palette_spread=0.0000, chroma_stddev=0.0000, hue_concentration=0.0000 | similar centroid color |
| 10 | KKSgb3837 | Udkast til en mandsdragt. Han bærer en lang stav med en fugl på toppen | 0.076569 | centroid_oklab=0.0766, palette_spread=0.0000, chroma_stddev=0.0000, hue_concentration=0.0000 | similar centroid color |

### visual-character-similarity-v1

| Rank | Object | Title | Distance | Contributions | Factual explanation |
|---:|---|---|---:|---|---|
| 1 | KKSgb209 | Stående rødbroget ko | 0.091565 | centroid_oklab=0.0530, palette_spread=0.0000, chroma_stddev=0.0000, hue_concentration=0.0000, brightness=0.0048, contrast=0.0022, saturation=0.0308, entropy=0.0007 | similar centroid color |
| 2 | KKSgb210 | Liggende rød- og sortbroget ko | 0.092230 | centroid_oklab=0.0530, palette_spread=0.0000, chroma_stddev=0.0000, hue_concentration=0.0000, brightness=0.0000, contrast=0.0076, saturation=0.0307, entropy=0.0009 | similar centroid color |
| 3 | KKS1977-473 | Motiv fra et østgrønlandsk sagn (Et fuglevæsen med barnehoved. Den ene af Andreassen-familiens to familietupilakker) | 0.097519 | centroid_oklab=0.0530, palette_spread=0.0000, chroma_stddev=0.0000, hue_concentration=0.0000, brightness=0.0041, contrast=0.0004, saturation=0.0400, entropy=0.0000 | similar centroid color |
| 4 | KKSgb13565 | Studie af apostlen Markus skrivende, samt detailstudie af hånden, der holder bogen | 0.105894 | centroid_oklab=0.0265, palette_spread=0.0118, chroma_stddev=0.0207, hue_concentration=0.0000, brightness=0.0001, contrast=0.0096, saturation=0.0369, entropy=0.0002 | similar centroid color |
| 5 | KKSgb96 | Vendet Mølle ved Dortheaslyst | 0.106721 | centroid_oklab=0.0265, palette_spread=0.0118, chroma_stddev=0.0207, hue_concentration=0.0000, brightness=0.0083, contrast=0.0095, saturation=0.0291, entropy=0.0008 | similar centroid color |
| 6 | KKS1974-43 | Studier af englebørns hoveder i en sky | 0.107220 | centroid_oklab=0.0265, palette_spread=0.0118, chroma_stddev=0.0207, hue_concentration=0.0000, brightness=0.0013, contrast=0.0000, saturation=0.0464, entropy=0.0004 | similar centroid color |
| 7 | KKSgb7710 | Studie efter Guido Renis freske i Cappella dell' Annunciazione, Palazzo Quirinale, Rom. (Marias fødsel, venstre side) | 0.109088 | centroid_oklab=0.0265, palette_spread=0.0118, chroma_stddev=0.0207, hue_concentration=0.0000, brightness=0.0106, contrast=0.0099, saturation=0.0256, entropy=0.0039 | similar centroid color |
| 8 | KKS13801 | Sappho og Mytilenerinden | 0.109548 | centroid_oklab=0.0530, palette_spread=0.0000, chroma_stddev=0.0000, hue_concentration=0.0000, brightness=0.0013, contrast=0.0048, saturation=0.0499, entropy=0.0006 | similar centroid color |
| 9 | KKSgb7665 | Mandlig modelstudie, halvtliggende | 0.110903 | centroid_oklab=0.0530, palette_spread=0.0000, chroma_stddev=0.0000, hue_concentration=0.0000, brightness=0.0070, contrast=0.0039, saturation=0.0461, entropy=0.0009 | similar centroid color |
| 10 | KKS1993-69 | Portræt af Antoinette Christiane Købke | 0.115676 | centroid_oklab=0.0594, palette_spread=0.0260, chroma_stddev=0.0037, hue_concentration=0.0032, brightness=0.0158, contrast=0.0042, saturation=0.0033, entropy=0.0000 | similar centroid color |

### geometry-similarity-v1

Not eligible: a required feature is null.

## KKSgb8124

Entity: `1170063127_object`. Title: Skitsebog nr. 29. Dresden 1845-1846.

Query features:

`{"centroid_a": 4.047642776505711e-11, "centroid_b": 1.8636953813544466e-08, "centroid_l": 0.4999999967367731, "chroma_stddev": 1.8636997767596426e-08, "hue_concentration_01": null, "log_net_area_cm2": null, "log_net_aspect_ratio": null, "log_net_height_cm": null, "log_net_width_cm": null, "palette_spread_oklab": 0.4999999967367734, "smk_brightness": 8.459217, "smk_contrast": 4.6236353, "smk_entropy": 7.400999, "smk_saturation": 1.0932152}`

### color-similarity-v1

| Rank | Object | Title | Distance | Contributions | Factual explanation |
|---:|---|---|---:|---|---|
| 1 | KKS12968 | Vinter vandløb ved en skov | 0.002207 | centroid_oklab=0.0022, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 2 | KKS11612 | C. P. Hansen | 0.002207 | centroid_oklab=0.0022, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 3 | KKSgb13111/27 | "Tiden afklædt" Nr. 3 | 0.033356 | centroid_oklab=0.0334, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 4 | KKSgb12947 | Frederik Adolph Mørck | 0.033356 | centroid_oklab=0.0334, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 5 | KKS10780 | To hekse slås om et kosteskaft | 0.034496 | centroid_oklab=0.0057, palette_spread=0.0288, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 6 | KMS6004 | Venus med æblet | 0.038755 | centroid_oklab=0.0088, palette_spread=0.0000, chroma_stddev=0.0299 | similar centroid color; hue concentration unavailable |
| 7 | KKSgb13111/15 | "Nøgle til adskillige Kobbere" | 0.039402 | centroid_oklab=0.0035, palette_spread=0.0359, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 8 | KKS3981 | Karl Mantzius | 0.041335 | centroid_oklab=0.0413, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 9 | KKS12012 | Vandkalv | 0.041767 | centroid_oklab=0.0168, palette_spread=0.0250, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 10 | KKS5374 | Henrik Ibsen | 0.041767 | centroid_oklab=0.0168, palette_spread=0.0250, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |

### visual-character-similarity-v1

| Rank | Object | Title | Distance | Contributions | Factual explanation |
|---:|---|---|---:|---|---|
| 1 | KKS12968 | Vinter vandløb ved en skov | 0.054169 | centroid_oklab=0.0015, palette_spread=0.0000, chroma_stddev=0.0000, brightness=0.0071, contrast=0.0164, saturation=0.0077, entropy=0.0215 | similar centroid color; hue concentration unavailable |
| 2 | KKS11612 | C. P. Hansen | 0.074956 | centroid_oklab=0.0015, palette_spread=0.0000, chroma_stddev=0.0000, brightness=0.0115, contrast=0.0147, saturation=0.0014, entropy=0.0459 | similar centroid color; hue concentration unavailable |
| 3 | KKS2514 | Abbaten og den spindende pige | 0.075098 | centroid_oklab=0.0016, palette_spread=0.0418, chroma_stddev=0.0000, brightness=0.0098, contrast=0.0008, saturation=0.0191, entropy=0.0021 | similar centroid color; hue concentration unavailable |
| 4 | KKSgb8340/36 | Figurkomposition | 0.086247 | centroid_oklab=0.0128, palette_spread=0.0055, chroma_stddev=0.0328, brightness=0.0118, contrast=0.0046, saturation=0.0077, entropy=0.0109 | similar centroid color; hue concentration unavailable |
| 5 | KMS5888 | Skuespillerinden Fru Johanne Dybwad | 0.090488 | centroid_oklab=0.0159, palette_spread=0.0480, chroma_stddev=0.0000, entropy=0.0266 | similar centroid color; hue concentration unavailable |
| 6 | KKSgb8340/30 verso | Kompositionsrids med figurer samlet omkring en himmelseng, forrest kvinder, der holder et draperi til side | 0.093108 | centroid_oklab=0.0083, palette_spread=0.0000, chroma_stddev=0.0270, brightness=0.0171, contrast=0.0049, saturation=0.0005, entropy=0.0353 | similar centroid color; hue concentration unavailable |
| 7 | KKSgb8353/20 verso | Sejlbåd med muntert selskab | 0.094134 | centroid_oklab=0.0153, palette_spread=0.0012, chroma_stddev=0.0380, brightness=0.0139, contrast=0.0048, saturation=0.0025, entropy=0.0185 | similar centroid color; hue concentration unavailable |
| 8 | KKS12129 | E. P. Bruhn | 0.096996 | centroid_oklab=0.0126, palette_spread=0.0218, chroma_stddev=0.0000, brightness=0.0002, contrast=0.0267, saturation=0.0128, entropy=0.0230 | similar centroid color; hue concentration unavailable |
| 9 | KKSgb11875/69 | Philoktet | 0.099265 | centroid_oklab=0.0257, palette_spread=0.0113, chroma_stddev=0.0302, brightness=0.0109, contrast=0.0035, saturation=0.0032, entropy=0.0144 | similar centroid color; hue concentration unavailable |
| 10 | KKSgb9874/35 | Stor marmorvase i gården ved S. Cecilia i Trastevere | 0.099491 | centroid_oklab=0.0203, palette_spread=0.0180, chroma_stddev=0.0288, brightness=0.0036, contrast=0.0087, saturation=0.0194, entropy=0.0006 | similar centroid color; hue concentration unavailable |

### geometry-similarity-v1

Not eligible: a required feature is null.

## KKSgb22323

Entity: `1170000125_object`. Title: Den besejrede Syphax stilles for Scipio.

Query features:

`{"centroid_a": 6.412081976492345e-11, "centroid_b": 2.952370570241669e-08, "centroid_l": 0.7920743356340977, "chroma_stddev": 0.0, "hue_concentration_01": null, "log_net_area_cm2": null, "log_net_aspect_ratio": null, "log_net_height_cm": null, "log_net_width_cm": null, "palette_spread_oklab": 0.0, "smk_brightness": 6.372257, "smk_contrast": 3.7947528, "smk_entropy": 9.792436, "smk_saturation": 1.6356592}`

### color-similarity-v1

| Rank | Object | Title | Distance | Contributions | Factual explanation |
|---:|---|---|---:|---|---|
| 1 | DEP971 | Første studie til billedet med kvinderne ved fontænen i A. | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 2 | KKSgb17345 | Studie til et portræt, formentlig af A. G. Moltke; til højre på bladet studie til Elefantridderordenens kæde | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 3 | KKSgb17357 | Diana og Aktæon (Ovids Metamorfoser) | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 4 | KKS7398 | En nøgen rytter i profil t.h. med et sværd i sin fremstrakte højre hånd | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 5 | KKSgb15957 | Tegning af en soldater statue | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 6 | KKSgb13571 | En kvinde med et skriftbånd i venstre og en murske i højre hånd, lænende sig til en himmelglobus | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 7 | KKSgb5608 | Hyrdernes tilbedelse | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 8 | KKSgb5695 | Syndefaldet | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 9 | KKS2507a | Jægeren | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 10 | KKS16441 | "Hververen" | 0.000000 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |

### visual-character-similarity-v1

| Rank | Object | Title | Distance | Contributions | Factual explanation |
|---:|---|---|---:|---|---|
| 1 | KKSgb22339 | Demetrius lider kvælningsdøden ved forgiftning | 0.031855 | centroid_oklab=0.0003, palette_spread=0.0182, chroma_stddev=0.0000, brightness=0.0072, contrast=0.0012, saturation=0.0049, entropy=0.0000 | similar centroid color; hue concentration unavailable |
| 2 | KKSgb22286 | Marcus Atilius Regulus dræber en serpent i Afrika | 0.032861 | centroid_oklab=0.0003, palette_spread=0.0182, chroma_stddev=0.0000, brightness=0.0074, contrast=0.0018, saturation=0.0051, entropy=0.0000 | similar centroid color; hue concentration unavailable |
| 3 | KKS524 | Foran en kirkedør | 0.038461 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000, brightness=0.0120, contrast=0.0006, saturation=0.0258, entropy=0.0000 | similar centroid color; hue concentration unavailable |
| 4 | KKSgb9916/1 | Syndfloden | 0.059172 | centroid_oklab=0.0003, palette_spread=0.0182, chroma_stddev=0.0000, brightness=0.0148, contrast=0.0060, saturation=0.0153, entropy=0.0046 | similar centroid color; hue concentration unavailable |
| 5 | KKSgb22377 | En edsaflæggelse (In dem Namen der heilig göttlichen untheilbaren Dreyfaltigheit) | 0.064404 | centroid_oklab=0.0307, palette_spread=0.0137, chroma_stddev=0.0000, brightness=0.0036, contrast=0.0055, saturation=0.0109, entropy=0.0000 | similar centroid color; hue concentration unavailable |
| 6 | KKSgb12083 | Stille vejr på havet | 0.064719 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000, brightness=0.0377, contrast=0.0264, saturation=0.0003, entropy=0.0003 | similar centroid color; hue concentration unavailable |
| 7 | KKSgb11683 | Genius med bue i venstre hånd og højre hånd hævet mod en kronet fugl | 0.065258 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000, brightness=0.0425, contrast=0.0195, saturation=0.0031, entropy=0.0002 | similar centroid color; hue concentration unavailable |
| 8 | KKSgb22243 | Kort over Rufach | 0.068672 | centroid_oklab=0.0003, palette_spread=0.0182, chroma_stddev=0.0000, brightness=0.0283, contrast=0.0190, saturation=0.0028, entropy=0.0000 | similar centroid color; hue concentration unavailable |
| 9 | KKS6235 | Kristus velsignende | 0.068706 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000, brightness=0.0439, contrast=0.0163, saturation=0.0085, entropy=0.0000 | similar centroid color; hue concentration unavailable |
| 10 | KKSgb13097 | Kunstnernes Karneval 1845 | 0.068901 | centroid_oklab=0.0000, palette_spread=0.0000, chroma_stddev=0.0000, brightness=0.0371, contrast=0.0181, saturation=0.0135, entropy=0.0003 | similar centroid color; hue concentration unavailable |

### geometry-similarity-v1

Not eligible: a required feature is null.

## KKS4443

Entity: `1170001489_object`. Title: Landskab med et slot på en klippe.

Query features:

`{"centroid_a": 4.904935485550155e-11, "centroid_b": 2.2584269431432286e-08, "centroid_l": 0.6059002314916988, "chroma_stddev": 1.1584399951969442e-08, "hue_concentration_01": null, "log_net_area_cm2": null, "log_net_aspect_ratio": null, "log_net_height_cm": null, "log_net_width_cm": null, "palette_spread_oklab": 0.2898124065098517, "smk_brightness": 6.3518715, "smk_contrast": 5.8650985, "smk_entropy": 8.599682, "smk_saturation": null}`

### color-similarity-v1

| Rank | Object | Title | Distance | Contributions | Factual explanation |
|---:|---|---|---:|---|---|
| 1 | KAS1333 | Kekrops og datter, Parthenons vestgavl, formindsket version | 0.004813 | centroid_oklab=0.0003, palette_spread=0.0045, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 2 | KMS5928 | Pigebarn, der piller tæer. Siddende nøgen kvinde | 0.004813 | centroid_oklab=0.0003, palette_spread=0.0045, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 3 | KMSsp325 | Dansen om majstangen | 0.004888 | centroid_oklab=0.0032, palette_spread=0.0017, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 4 | KKS12165 | Hans Egede | 0.005791 | centroid_oklab=0.0015, palette_spread=0.0042, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 5 | KKS9619e | Illustration til H. Drachmann, "Marts" | 0.007100 | centroid_oklab=0.0057, palette_spread=0.0014, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 6 | KAS66 | Galler dræber sin hustru og sig selv, Paetus og Arria | 0.012158 | centroid_oklab=0.0011, palette_spread=0.0111, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 7 | KAS440 | Buste fra profetstatue, Il Zucchone | 0.012158 | centroid_oklab=0.0011, palette_spread=0.0111, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 8 | DEP454 | Portræt af Antinoos med vedbendkrans | 0.012158 | centroid_oklab=0.0011, palette_spread=0.0111, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 9 | KAS2272 | Fra statuen af Athena Parthenos | 0.012158 | centroid_oklab=0.0011, palette_spread=0.0111, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |
| 10 | KAS2232 | Davids hoved | 0.012158 | centroid_oklab=0.0011, palette_spread=0.0111, chroma_stddev=0.0000 | similar centroid color; hue concentration unavailable |

### visual-character-similarity-v1

| Rank | Object | Title | Distance | Contributions | Factual explanation |
|---:|---|---|---:|---|---|
| 1 | KMSr123 | Siddende nøgen kvinde. Leda | 0.021815 | centroid_oklab=0.0109, palette_spread=0.0018, chroma_stddev=0.0000, brightness=0.0045, contrast=0.0017, entropy=0.0030 | similar centroid color; hue concentration unavailable |
| 2 | KMSsp325 | Dansen om majstangen | 0.022439 | centroid_oklab=0.0024, palette_spread=0.0011, chroma_stddev=0.0000, brightness=0.0044, contrast=0.0050, entropy=0.0095 | similar centroid color; hue concentration unavailable |
| 3 | KKS11053 | Peter R. Saabye | 0.026205 | centroid_oklab=0.0097, palette_spread=0.0046, chroma_stddev=0.0000, entropy=0.0118 | similar centroid color; hue concentration unavailable |
| 4 | KKSgb5490 | Udsigt af den offentlige promenade af Hr. Conferenceråd Classen anlagt uden Københavns Østerport | 0.039989 | centroid_oklab=0.0186, palette_spread=0.0189, chroma_stddev=0.0000, entropy=0.0025 | similar centroid color; hue concentration unavailable |
| 5 | KMS959 | Ruiner i Den romerske Campagne | 0.042034 | centroid_oklab=0.0018, palette_spread=0.0221, chroma_stddev=0.0000, brightness=0.0062, contrast=0.0026, entropy=0.0093 | similar centroid color; hue concentration unavailable |
| 6 | KMS6195 | Dameportræt | 0.042190 | centroid_oklab=0.0023, palette_spread=0.0212, chroma_stddev=0.0000, brightness=0.0085, contrast=0.0062, entropy=0.0041 | similar centroid color; hue concentration unavailable |
| 7 | KKS19998/5 | Blank | 0.047098 | centroid_oklab=0.0078, palette_spread=0.0176, chroma_stddev=0.0000, brightness=0.0023, contrast=0.0002, entropy=0.0191 | similar centroid color; hue concentration unavailable |
| 8 | KMS1036 | Stående brun hest | 0.047324 | centroid_oklab=0.0166, palette_spread=0.0007, chroma_stddev=0.0000, brightness=0.0030, contrast=0.0160, entropy=0.0110 | similar centroid color; hue concentration unavailable |
| 9 | KKSgb13265 | Palmeofring. En ægyptisk kvinde på vej til hendes mands grav med en palmegren, efter østerlandsk skik | 0.051326 | centroid_oklab=0.0018, palette_spread=0.0218, chroma_stddev=0.0000, brightness=0.0137, contrast=0.0103, entropy=0.0037 | similar centroid color; hue concentration unavailable |
| 10 | KMS759 | Eftermiddag ved Himmelbjerget | 0.052000 | centroid_oklab=0.0312, palette_spread=0.0186, chroma_stddev=0.0000, entropy=0.0022 | similar centroid color; hue concentration unavailable |

### geometry-similarity-v1

Not eligible: a required feature is null.


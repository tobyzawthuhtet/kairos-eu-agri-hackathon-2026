# Olive scenarios 01: dormancy -> bud-break -> inflorescence development (Dec-May)

Status: research pass 2 (deep). Every number below was read in a fetched primary source (PDF or page text), not a search snippet, unless marked "snippet". "NAV" = needs agronomist validation (no source found; what was searched is stated). All CSV rows are `validated=false`: sources are official or peer-reviewed, but no Kairos agronomist has signed off. Machine-readable version: `csv/01_dormancy_to_budbreak.csv` (56 trigger rows: 48 with a cited threshold, 8 NAV). Scenario IDs are `OLV-S0<stage>-<HAZARD>-<nn>`.

Regions: Andalucia (AN), Castilla-La Mancha (CM), Extremadura (EX), Cataluna (CT), Comunitat Valenciana (VC).

## Sources (all fetched and read)

| ID | Source | URL |
|---|---|---|
| G1 | MAPA, Guia de Gestion Integrada de Plagas: Olivar (2014; national, basis of regional PI rules; full text read) | https://www.mapa.gob.es/dam/mapa/contenido/agricultura/temas/medios-de-produccion/productos-fitosanitarios/uso-sostenible-de-productos-fitosanitarios/guias-de-gestion-integrada-de-plagas/guiaolivar--2-.pdf |
| A1 | AEMET, Plan Meteoalerta, Anexo 1 Umbrales y niveles de aviso, v1 31-may-2022, zone tables | https://www.aemet.es/documentos/es/eltiempo/prediccion/avisos/plan_meteoalerta/METEOALERTA_ANX1_Umbrales_y_niveles_de_aviso.pdf |
| D1 | De Melo-Abreu, Barranco, Cordeiro, Tous, Cruz 2004, Modelling olive flowering date using chilling for dormancy release and thermal time, Agric. For. Meteorol. 125:117-127 (full text read) | https://www.sciencedirect.com/science/article/abs/pii/S016819230400070X |
| S1 | Frontiers in Plant Science 2024, frost tolerance methodology in olive (full text read) | https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2024.1397534/full |
| M1 | MAPA / Agricultura 2004 (869:958-963), Evaluacion de la tolerancia a helada de diez variedades de olivo (full text read) | https://mapa.gob.es/ministerio/pags/biblioteca/revistas/pdf_Agri/Agri_2004_869_958_963.pdf |
| F17 | Torres et al. 2017, Frontiers Plant Sci 8:1830, olive in the Southern Hemisphere (chilling section) | https://www.frontiersin.org/articles/10.3389/fpls.2017.01830/pdf |
| C1 | IOC World Olive Germplasm catalogue, chilling classes (column mapping garbled in extraction) | https://worldolivecatalogue.internationaloliveoil.org/es/node/472 |
| H1 | Hueso, Camacho, Gomez-del-Campo 2021, Agric. Water Manag. 248:106695 (abstract via AGRIS) | https://agris.fao.org/search/ar/records/65dfee910f3e94b9e5ddb1aa |
| P1 | ISHS Acta Hort 1231: olive pollen germination at 15-35 C (abstract) | https://ishs.org/ishs-article/1231_9/ |
| S3 | Metos, olive peacock spot model summary | https://metos.global/en/disease-models-olive/ |
| S4 | UC IPM peacock spot | https://ipm.ucanr.edu/agriculture/olive/peacock-spot |
| S5 | Rodrigues et al. 2017, Prays oleae degree-day model, Dao (Portugal) | https://revistas.rcaap.pt/rca/article/view/16547 |
| R1 | RAIF Huelva olive bulletin 13-17 May 2024 | https://www.juntadeandalucia.es/agriculturapescaaguaydesarrollorural/raif/wp-content/uploads/2023/03/Informe_EspecialInteres_Olivar-2.pdf |
| R2 | RAIF repilo recommendations 27-03-2025 (restates G1) | https://www.juntadeandalucia.es/agriculturapescaaguaydesarrollorural/raif/wp-content/uploads/2023/09/Recomendaciones-para-el-Repilo-27-03-2025.pdf |

Regional-guide coverage (honest status): the national GIP guide G1 is the binding template for all regional Produccion Integrada rules (RD 1311/2012), and Andalucia's RAIF applies it (R1, R2). I could NOT retrieve the text of the Castilla-La Mancha, Extremadura, Cataluna (IRTA/DARP) or Comunitat Valenciana (GVA/IVIA) olive PI norms: searches returned unrelated DOE (Extremadura, Orden 23-12-2003 / modification 29-06-2010 exist but the fetched DOE PDFs were other documents), CLM bulletin URLs returned 404/HTML, IRTA PDF was an event programme (only mention: Bacillus thuringiensis session for Prays oleae, Nov 2025), and GVA returned no olive PI text. Thresholds are therefore national/Andalucia-level and flagged for regional check. IOC technical guides and Orlandi et al. (Umbria/Andalusia chilling) were searched but only paywalled/403 abstracts were reachable; ResearchGate, ScienceDirect, MDPI, HortScience (Barranco 2005) returned 403.

## 1. Calendar windows

Stage definitions use the GIP phenology letters: B yema movida (bud swell), E-F stamens visible to start of flowering, G fruit set (G1 pp. 61-63).

| Stage | Window | Evidence |
|---|---|---|
| 1 Dormancy / chilling | Chill accumulation from 1 Oct in the De Melo-Abreu model; Cordoba normally satisfied by about end Jan (D1) | D1. IOC catalogue lists dates 20 Feb-6 Mar per cultivar (header lost in extraction: NAV meaning) |
| 2 Bud-break, shoot growth | After dormancy release; phyllophagous Prays sampling at stage B (G1) | G1. Calendar months per region: NAV |
| 3 Inflorescence development to bloom | Mean full flowering (50% open): Cordoba 9-12 May (DOY 129-132), Elvas (PT, near Extremadura) 11-19 May, Mas Bove, Reus (Tarragona) 18 May (Arbequina, Picual) | D1 Table 2. Warm years advance this: Huelva 2024 was already stage G2 (fruit set) by mid-May (R1); 1 C warming advances flowering 5-8 days (D1) |

Valencia and Castilla-La Mancha flowering dates: NAV (no retrieved dataset). Thermal time from dormancy release to full flowering: about 460-510 C-days above base 9.1 C (D1 Table 3/4).

## 2. Key sensitivities (sourced)

| Stage | Sensitivities |
|---|---|
| 1 Dormancy | Chilling releases flower buds from dormancy; insufficient chill gives delayed/irregular flowering and deformed buds (D1, F17). Hours above 20.7 C cancel accumulated chill (D1). Frost: plantlet critical temp -7 +/-1 C; tree damage below -7 C and death below -12 C (S1, M1); de-acclimated trees are damaged at -4.7 to -6.4 C (S1). Hardiness peaks Jan-Feb (Antognozzi cited in M1); autumn frosts hurt more than winter ones (M1). Cultivar: Cornicabra most resistant in field test (45% stems frozen), Arbequina 63%, Hojiblanca/Picual/Manzanilla Cacerena intermediate, Empeltre/Frantoio worst (M1). Repilo infects in humid autumn-winter (G1). |
| 2 Bud-break | Repilo: new leaves more sensitive, re-sample second half of spring in rainy springs (G1). Prays phyllophagous generation negligible except young plantations (G1). Young-shoot frost threshold NAV. Spring water deficit cuts shoot growth, flowering and yield; best yield when midday stem water potential stays above -1.0 MPa (H1). |
| 3 Inflorescence | Frost on inflorescences: 2 C quoted as danger threshold, losses up to 95% (Zucchini 2023 via S1). Water stress at flowering is the most yield-sensitive point (H1). Pollen germination peaks near 30 C and falls at 35 C (P1). Prays anthophagous generation feeds on flower buds Apr-May (G1). Algodoncillo (psyllid) can impair fertilisation in dense colonies at flowering (G1). |

## 3. Scenario -> action tables

Severity L/M/H. Lead time in hours (CSV `action_lead_time_h`; lead times and actions are Kairos design choices informed by the sources, not source values). Conf = confidence in the threshold. Thresholds marked "warn" are AEMET warning levels, not crop-damage levels.

### Stage 1: Winter dormancy / chilling

| Scenario ID | Trigger | Source | Sev | Action | Lead h | Conf |
|---|---|---|---|---|---|---|
| OLV-S01-FROST-01 | Tmin <= -7 C (30 min lab; field duration NAV) | S1, M1 | H | Do not prune/clear frost-hit wood until regrowth; defer N; Cu on wounds if frost/hail forecast or just occurred (olive knot, G1) | 72 | Med |
| OLV-S01-FROST-02 | Tmin <= -12 C (tree death; leaf LT50 -12, shoot LT50 -18 hardened) | M1 | H | Damage survey, delayed renovation pruning | 72 | Med |
| OLV-S01-FROST-03 | Tmin <= -4.7 C after unusually warm late winter (de-acclimated) | S1 | H | Raise frost alert; postpone pruning | 72 | Low |
| OLV-S01-FROST-04 | Warm-spell definition for deacclimation (Tmax/14 d) | NAV | M | as above | 72 | Low |
| OLV-S01-WARN-COLD-01/02/03 | AEMET yellow Tmin warn: -1 C coastal/low zones (Campina cordobesa/sevillana, Andevalo, Catalan and Valencian litoral); -4 C inland (Jaen, Cordoba sierras, CLM, Extremadura, Lleida/Tarragona/Barcelona depression, Valencia interior sur); -6 C (Cuenca, Valencia interior norte, Castellon interior). Orange/red are 4-8 C lower (A1) | A1 | L-M | Frost watch, compare with crop thresholds | 48 | High (warn) |
| OLV-S01-CHILL-01..04 | Cumulative chill units (model 1, from 1 Oct) below cultivar requirement at ~end Jan: Arbequina 339 U, Manzanilla de Sevilla 433 U, Picual 469 U, Hojiblanca 494 U | D1 Tables 3-4 (To 7.3 C, Tx 20.7 C, a -0.56) | M | Expect delayed/irregular bloom; avoid heavy pruning, balanced N/irrigation | 720 | Med |
| OLV-S01-CHILL-05..08 | Alt. chill hours below 7 C: Arbequina 221 h, Manzanilla 210 h, Picual 203 h, Hojiblanca 177 h | D1 Tables 3-4 | M | same | 720 | Med |
| OLV-S01-CHILL-09 | Cornicabra requirement: only class "medium" (IOC catalogue); units NAV | C1 | M | same | 720 | Low |
| OLV-S01-CHILL-REV-01 | Tair > 20.7 C removes 0.56 U per hour (also ~21 C partial reversal, F17) | D1, F17 | M | Track net units; warn on warm spells | 168 | Med |
| OLV-S01-CHILL-REV-02 | Warm winter early budswell (Tmean) | NAV | M | Delay pruning | 168 | Low |
| OLV-S01-RAIN-01 | Rain >= 40 mm/12 h (60 mm/12 h Catalan/Valencian coastal zones), AEMET yellow warn; agronomic waterlogging NAV | A1 | M | Drainage, avoid traffic, delay fertilising/Cu | 48 | Med |
| OLV-S01-WLOG-01, DROUGHT-01 | soil saturation days; winter precip % of normal | NAV | M | drain; plan irrigation | 72/336 | Low |
| OLV-S01-REPILO-01 | RH > 98% or rain on leaves 1-2 d at 15-20 C | G1 | M | Aeration pruning, avoid excess N | 72 | High |
| OLV-S01-REPILO-02/03 | Leaf wetness >= 9 h at 15-20 C; >= 12 h at 10 C; >= 24 h at 5 C; optimum 16-21 C | S3 (S4: ~2 d typical, 14 h min when warm, California) | M | as above | 48 | Med |
| OLV-S01-REPILO-DEC-01 | >1% leaves with visible/latent repilo at end-winter sample (20 trees x 20 leaves); preventive treatment if prior attack >1% and weather favourable | G1, R2 | M | Preventive or translaminar fungicide per infestation; resistant cultivars Lechin de Sevilla, Manzanilla de Hellin, Picudo de Montoro | 72 | High |
| OLV-S01-HAIL-01 | Strong storm with hail > 1 cm (AEMET yellow); no olive damage threshold | A1 | M | Inspect; Cu on wounds (G1) | 24 | Med |
| OLV-S01-WIND-01 | Gust >= 70 km/h (AEMET yellow; 80 in Ampurdan, Cuenca Serrania, Valencia/Castellon interior); crop threshold NAV | A1 | L | Secure structures; no burning/spraying | 24 | Med |

### Stage 2: Bud-break and shoot growth

| Scenario ID | Trigger | Source | Sev | Action | Lead h | Conf |
|---|---|---|---|---|---|---|
| OLV-S02-FROST-01 | Tmin <= -4.7 C after warm late winter (vegetative restart; -4.7 to -6.4 and -7.6 C heavier damage) | S1 | H | Frost alert; delay pruning/tillage; Cu on wounds | 72 | Low |
| OLV-S02-FROST-02 | Young shoot/leaf threshold | NAV (searched S1, M1, G1, R1; only a non-primary Chile/Argentina web text says just below 0 C) | H | Frost alert | 72 | Low |
| OLV-S02-REPILO-DEC-01 | >1% leaves repilo; resample 2nd half of spring in rainy springs | G1 | M | Preventive treatment before rain | 72 | High |
| OLV-S02-REPILO-04 | Leaf wetness >= 9 h at 15-20 C | S3 | M | same | 48 | Med |
| OLV-S02-PRAYS-PHY-01 | >20% attacked shoots (10 shoots x 20 trees, stage B), only in plantations in formation, when live larvae seen; adult groves: no treatment | G1 | L | Monitor; conserve auxiliary fauna | 120 | High |
| OLV-S02-DROUGHT-01 | Midday stem water potential < -1.0 MPa before irrigation (best yield above -1.0); Arbequina hedgerow, central Spain | H1 | M | Start/advance irrigation | 168 | Med |
| OLV-S02-DROUGHT-02, HEAT-01 | soil-water % capacity; spring heat Tmax | NAV | M | irrigate | 168/96 | Low |
| OLV-S02-RAIN-01 | Rain >= 40 mm/12 h (AEMET yellow) | A1 | M | Drainage, delay fertilising | 48 | Med |
| OLV-S02-VERTI-01 | Verticillium: GIP states no intervention threshold | G1 | L | Remove/destroy affected parts, avoid excess N and waterlogging, solarise | 168 | High |
| OLV-S02-HAIL-01, WIND-01 | hail > 1 cm; gust >= 70 km/h (AEMET) | A1 | M/L | inspect/Cu; delay sprays | 24 | Med |

### Stage 3: Inflorescence development

| Scenario ID | Trigger | Source | Sev | Action | Lead h | Conf |
|---|---|---|---|---|---|---|
| OLV-S03-FROST-01 | Tmin <= 2 C on inflorescences (early-April event, Italy, up to 95% loss; exposure time not reported) | S1 citing Zucchini 2023 | H | Frost alert; no pruning/tillage/herbicide | 72 | Low |
| OLV-S03-FROST-02 | Night minima: max flowering at 4.4-7.8 C; reduced at 2.2 C (greenhouse, Arbequina) | F17 | L | Informational | 72 | Low |
| OLV-S03-PHEN-01..04 | Thermal time to full flowering (base 9.1 C): Manzanilla de Sevilla 488, Arbequina 490, Picual 495, Hojiblanca 510 C-days | D1 | M | Time frost watch and scouting | 120 | Med |
| OLV-S03-HEAT-01 | Tmax >= 35 C (pollen germination and tube growth lower at 35 C than 30 C; 24 h in vitro; Croatian cultivars) ; field duration NAV | P1 | M | Irrigate, avoid sprays | 72 | Low |
| OLV-S03-DROUGHT-01/02 | Midday stem water potential < -1.5 MPa (oil 64% of max) and < -1.7 MPa (oil halved) at flowering | H1 | H | Irrigate; do not suspend | 168 | Med |
| OLV-S03-PRAYS-ANT-01/02 | Inflorescences with live forms >= 5% AND < 10 inflorescences per shoot, at 20% open flowers (10 inflorescences x 20 trees, stages E-F) | G1 | M | Treat only if both met; fauna-friendly products | 120 | High |
| OLV-S03-PRAYS-DD-01 | Degree-days 169-389 = first generation, which is anthophagous (Dao, Portugal; base not stated; 2nd gen carpophagous 436-778) | S5 | L | Plan scouting only | 120 | Low |
| OLV-S03-EUPHY-01 | Algodoncillo >= 8 insects per inflorescence (10 trees x 10 inflorescences at start of flowering) | G1 | L | Scout if abundant; no chemicals authorised at guide date | 96 | High |
| OLV-S03-REPILO-01 | Leaf wetness >= 9 h at 15-20 C | S3 | M | Preventive treatment before rain | 48 | Med |
| OLV-S03-RAIN-01, HAIL-01, WIND-01 | Rain >= 40 mm/12 h; hail > 1 cm; gust >= 70 km/h (AEMET yellow warn) | A1 | M/L | drainage; assess; irrigate ahead | 24-48 | Med |

Corrections to the earlier draft: Prays generation 1 (169-389 DD, S5) is the anthophagous generation, not phyllophagous; GIP protocol uses no traps and no degree-days. The earlier "2 C inflorescence" claim is now traced to Zucchini et al. 2023 via S1 (Olivonews page timed out on re-fetch). Draft values for Cu timing at 9-12 h wetness, -3 C deacclimation frost, Tmax 15 C x 5 d, 30/32-35 C spring heat, 70/60/40 km/h crop wind, 50 mm/48 h waterlogging, 60% winter precipitation, 10-20% shoot infestation and 20-30% ETc irrigation were NOT supported by any fetched source and are removed or NAV.

## 4. Variables and resolution needed

| Trigger | Variables | Resolution | Layer | Horizon |
|---|---|---|---|---|
| Frost | Tmin 2 m, hourly T, wind/cloud (radiative), warm-spell history 14 d | Hourly | Parcel + DEM cold-air pooling | 1-5 d (alert 72 h) |
| Chilling | Hourly T from 1 Oct (model 1 units and h<7 C), cultivar TU | Hourly -> season | Station/grid | Season + outlook |
| Bloom timing | Daily T, GDD base 9.1 C after dormancy release | Daily | Grid | 7-14 d |
| Heat | Hourly T (35 C pollen) | Hourly | Grid | 3-7 d |
| Water stress | Midday stem potential (needs sensor/model), soil moisture 0-100 cm, ET0, P | Daily | Soil layers | 7-14 d |
| Rain / hail / wind | Precip 12 h and 1 h, hail/storm warning, gust 10 m | Hourly/nowcast | Grid / warning zone | 0-72 h |
| Repilo | Hourly RH, rain, leaf-wetness proxy, T 15-20 C; field % infected leaves | Hourly + 2 field samples | Station/grid | 3-5 d |
| Prays / algodoncillo | Phenology stage (B, E-F, G), field counts | Weekly samples | Parcel | 7 d |

## 5. Open items for the agronomist (remaining NAV)
1. Chilling units/hours for Cornicabra (class only) and for Empeltre/Arbosana; confirm model 1 vs h<7 C choice and end-Jan checkpoint.
2. Frost on young shoots/new leaves (OLV-S02-FROST-02), exposure duration for the 2 C inflorescence threshold, warm-spell definition for deacclimation (OLV-S01-FROST-04).
3. Regional PI norms for Castilla-La Mancha, Extremadura, Cataluna (IRTA/DARP) and Valencia (GVA/IVIA): confirm they match G1 thresholds (repilo >1%, Prays >=5% and <10 inflorescences/shoot, algodoncillo 8/inflorescence).
4. Soil-water triggers per soil type and system; winter waterlogging and drought criteria; whether midday stem potential thresholds (one Arbequina hedgerow site) apply to Picual, Hojiblanca and rainfed groves.
5. Crop-damage thresholds for wind, hail, heat spell in spring, winter warm-spell budswell (AEMET warning levels are not agronomic thresholds).

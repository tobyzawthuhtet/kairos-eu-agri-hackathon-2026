# Olive scenarios 02: Flowering -> Fruit set -> Pit hardening (May-Aug)

Scope: Andalucía, Castilla-La Mancha (CLM), Extremadura, Cataluña, Comunitat Valenciana.
Status: second (deep) pass. Documents were fetched and read (PDF text extracted with pdftotext where WebFetch could not decode) unless marked "snippet-only". Machine-readable version: `csv/02_flowering_to_pit_hardening.csv` (44 trigger rows, `validated=false` everywhere; no agronomist has signed off).
Rule: every number carries an `[Sx]` tag with a URL in section 0. Anything without a tag is **NAV (needs agronomist validation)**. Lead times (hours) in the CSV are system-design assumptions, not agronomic values.

## 0. Sources (all URLs fetched/read unless noted)
| Tag | Source | URL | What was used |
|---|---|---|---|
| S1 | AEMET, Plan Meteoalerta Anexo 1 "Umbrales y niveles de aviso", v1, 31-may-2022 | https://www.aemet.es/documentos/es/eltiempo/prediccion/avisos/plan_meteoalerta/METEOALERTA_ANX1_Umbrales_y_niveles_de_aviso.pdf | Tmax warning levels per zone; gust and rain levels; hail definition. A later version may have changed some zones (not checked). |
| S2 | Dias et al. 2022, Aust. J. Crop Sci. 16(9):1094-1100 (INIA Uruguay; Arbequina, Arbosana, Manzanilla, Picual, Koroneiki) | https://www.cropj.com/dias_16_9_2022_1094_1100.pdf | In-vitro pollen germination 0-40 C |
| S3 | Hueso, Camacho, Gómez-del-Campo 2021, Agric. Water Manage. 248 (Arbequina hedgerow, Central Spain, 5 yr) (abstract page read, full text not) | https://ideas.repec.org/a/eee/agiwat/v248y2021ics0378377420322393.html | SWP at flowering and after flowering; spring deficit levels |
| S4 | Martín-Palomo et al. 2020, Agronomy 10(2):258 (Manzanilla table olive, Sevilla, 3 seasons) full text | https://oa.upm.es/86330/1/6112191.pdf (doi:10.3390/agronomy10020258) | Control SWP targets; -2.0 MPa threshold; 25/50/100% ETc rule |
| S5 | Corell et al. 2020, Agric. Water Manage. (Manzanilla, Sevilla 2015-17) abstract page | https://oa.upm.es/86759/ | RDI SWP levels -2 / -3.5 MPa; pit hardening dates; 12 t/ha remark |
| S6 | Junta de Andalucía, "Estrategias de manejo de la mosca del olivo en Andalucía, campaña 2024" (June 2024) full text | https://www.juntadeandalucia.es/agriculturapescaaguaydesarrollorural/raif/wp-content/uploads/2023/09/ESTRATEGIA-DE-MANEJO-DE-LA-MOSCA-DEL-OLIVO.pdf | PI and GIP fly thresholds (table vs mill); kaolin dose; trapping |
| S7 | RAIF Boletín Fitosanitario Málaga olivar, 16-20 Jun 2025 | https://www.juntadeandalucia.es/agriculturapescaaguaydesarrollorural/raif/wp-content/uploads/2023/09/Informe_Fitosanitario_0616_0622-7.pdf | Prays carpófaga RPI threshold; fly receptivity and temperature |
| S8 | RAIF Boletín Fitosanitario Málaga olivar, 28 Apr-2 May 2025 | https://www.juntadeandalucia.es/agriculturapescaaguaydesarrollorural/raif/wp-content/uploads/2025/06/Informe_Fitosanitario_0428_0504-4.pdf | Prays antófaga RPI threshold (flowering) |
| S9 | MAPA, Vida Rural 276 (2008) pp. 44-48 | https://mapa.gob.es/ministerio/pags/biblioteca/revistas/pdf_Vrural/Vrural_2008_276_44_48.pdf | Prays thresholds; egg viability vs RH |
| S10 | Consejería de Agricultura CLM, Boletín fitosanitario nº5, 29 Jul 2024 (hosted on bandomovil.com) | https://bandomovil.com/userFiles/r1/r1nnxBOLETINDEAVISOSFITOSANITARIOSCLMN05.pdf | Fly temperature limits; patch 1%; full spray 5-7%; kaolin max 1 application |
| S11 | Tena et al. 2008, Bol. San. Veg. Plagas 34:211-217 (Valencia, citrus and olive) | https://mapa.gob.es/ministerio/pags/Biblioteca/Revistas/pdf%5FPlagas%2FBSVP%5F34%5F02%5F211%5F217%2Epdf | Saissetia oleae phenology, heat mortality, treatment timing |
| S12 | Calderón et al. 2014, PLoS ONE 9(10):e110664 (IAS-CSIC Córdoba) | https://quantalab.ias.csic.es/pdf/PlosOne_09_10_e110664_14.pdf | Verticillium vs soil temperature |
| S13 | FAO-56 Table 12 (Allen et al. 1998) | https://www.fao.org/4/x0490e/x0490e0b.htm | Olive Kc 0.65 / 0.70 / 0.70 (40-60% cover) |
| S14 | De Melo-Abreu et al. 2004, Agric. For. Meteorol. 125:117-127 (file read, not fetched via web) | https://doi.org/10.1016/j.agrformet.2004.02.009 | Base temperature 9.1 C; 460-510 C d to full flowering |
| S15 | GVA Portal Agrari, Avís nº1 mosca de l'olivera, 9-Sep-2025 | https://portalagrari.gva.es/documents/366567370/395345354/Av%C3%ADs+n%C2%BA+1+Mosca+de+la+olivera+09-09-2025.pdf/db91fe14-acc9-2b13-4e93-0b886908b77a | SNIPPET-ONLY: server refused the connection; content known only from a search summary |
| S16 | La Selva del Camp (Tarragona) fruit-fly advisory | https://www.laselvadelcamp.cat/sites/default/files/avisos/octubre_79.pdf | SNIPPET-ONLY: fetch returned 404; 5% punctured olives (2014 advisory) |
| S17 | Carried over from first draft, NOT re-read: Xylella vector surveys (https://helvia.uco.es/handle/10396/20192; https://ricerca.uniba.it/handle/11586/473326); IOC high-temperature node https://worldolivecatalogue.internationaloliveoil.org/es/node/470 | | See notes in section 5 |

## 1. Calendar windows
Drive by phenology (BBCH) or thermal time, not by date.
- Thermal time: base temperature 9.1 C; 460-510 C d accumulated from end of endodormancy to full flowering, depending on cultivar (Arbequina 490, Hojiblanca 510, Picual 495) [S14].
- Pit hardening: began 10-17 June and ran to the last week of August near Sevilla (Manzanilla, 2014-16) [S4, S5]. In the Central Spain (CLM) Arbequina trials deficit treatments ran from shoot growth (April-May) to pit hardening in early July [S3]. Fly oviposition becomes possible when fruit reaches pit hardening / about 10 mm (8-10 mm in CLM) [S7, S10].
- Flowering: Andalusian Prays antófaga generation coincides with bloom, end of April to June depending on zone [S8].
- Region-specific start/end dates for Extremadura, Cataluña, C. Valenciana: **NAV** (no PI phenology table found). The earlier draft's calendar table was approximate and is dropped; fruit set window (about 2-4 wk after full bloom) is NAV.

## 2. Key sensitivities
| Stage | Sensitivity |
|---|---|
| Flowering | In vitro, pollen germination peaks at 26.7 C (43%), 36% at 20 C, 22% at 15 C, only 15% at 40 C, none at 10 C; tube growth max at 28.2 C, optimum range 25-30 C [S2]. Field heat thresholds in Spain: **NAV** (the earlier "30 C reduces / 35 C kills flowers" claim from the IOC page could not be re-found: the fetched IOC node 470 gave only qualitative statements, "high temperatures accelerate and shorten flowering; extreme temperature or high humidity can disrupt pollination") [S17]. Water: oil production fell to 64% of maximum when midday SWP < -1.5 MPa in spring and was halved at -1.7 MPa; flowering is the most sensitive period to deficit [S3]. |
| Fruit set | Between end of flowering and pit hardening SWP could fall to -1.8 MPa with no effect on fruit drop, size or oil; fruit drop increased only below -2.71 MPa [S3]. Share of flowers that set: NAV. |
| Pit hardening | Yield not significantly affected by RDI of -2 or -3.5 MPa in table olive Manzanilla, but fruit drop and fruit size related to stress; RDI feasible up to 12 t/ha without losing fruit size [S5]. Oil-olive thresholds may not transfer to table olives (Corell 2020, see S5 page). |

## 3. Scenario tables
CSV scenario IDs in brackets.

### 3a. Flowering / anthesis
| Scenario | Trigger | Severity | Action | Lead time | Confidence |
|---|---|---|---|---|---|
| Heat, pollen optimum exceeded [OLV-S05-HEAT-01] | Tmax >= 30 C (upper end of in-vitro optimum) [S2] | Low | Monitor; keep SWP >= -1.2 MPa [S4] | 3-7 d | Low (in vitro, Uruguay) |
| Heat, strong [HEAT-02] | Tmax >= 35 C: value **NAV**, interpolated between 30 and 40 C [S2]; duration NAV | Medium | Avoid additional stress; log | 3-7 d | Low |
| Heat, critical [HEAT-03] | Tmax >= 40 C: pollen germination 15% vs 43% at optimum [S2] | High | No pollination rescue exists; log for yield forecast | 3-7 d | Low |
| Official heat alert [AEMET-Y38/Y36/O40/O39/R44/R42] | Meteoalerta Tmax. 38/40/44 C yellow/orange/red in Campiña cordobesa, Campiña sevillana, Valle del Guadalquivir de Jaén, La Mancha de Ciudad Real, La Mancha toledana, Vegas del Guadiana (Badajoz), Meseta cacereña, Interior sur de Valencia, Interior de Alicante. 36/39/42 C in Depresión central de Lleida and de Tarragona, Interior/Litoral norte de Valencia, La Mancha albaceteña and conquense [S1] | Medium/High/Critical | Use as alert layer on top of agronomic triggers | 1-5 d | High (official levels; not agronomic damage thresholds) |
| Hot dry wind [WIND-01] | **NAV** (no source on stigma desiccation; AEMET gust levels 70/90/130 km/h are damage levels [S1]) | Medium | NAV | 1-3 d | Low |
| Rain / high RH at bloom [RAIN-01] | **NAV** (searched: IOC, regional guides, Prays bulletins; no numeric trigger) | Medium | NAV | 1-5 d | Low |
| Water deficit pre-bloom [DROUGHT-01/02] | Midday SWP < -1.5 MPa (oil 64% of max); < -1.7 MPa (50%) [S3]. Target: SWP >= -1.2 MPa before massive pit hardening [S4] | High / Critical | Irrigate to ~100% ETc from pre-bloom; hold SWP >= -1.2 MPa | 7-14 d | Medium (Central Spain, Arbequina hedgerow; other cultivars/systems NAV) |
| Spring frost [FROST-01] | **NAV** | High | flag only | 1-3 d | Low |
| Prays antófaga [PRAYS-01] | Treat only if >= 5% inflorescences with live forms AND < 10 inflorescences/shoot AND < 20% fertile flowers [S8, S9]. Málaga 2025: 10.1% attacked but 6.2 inflorescences/shoot and 27% fertile flowers, so not met [S8] | Medium | Intervene only if all three conditions are met; preserve natural enemies | 7-14 d | High (Andalusian RPI) |
| Verticillium [VERT-01] | Soil 16-24 C promotes infection by defoliating pathotype in Picual (20-24 C in Arbequina); non-defoliating 16-20 C; optimum 24 C [S12] | Medium | No curative action sourced (**NAV**); avoid overwatering, prefer tolerant cultivars (NAV) | weeks | Medium |
| Xylella vectors [XYL-01] | Nymph peak 100-270 degree-days (Italy) [S17, not re-read]; only in affected zones (Baleares, Alicante, Madrid) | Medium | NAV | 1-3 wk | Low |

### 3b. Fruit set (June)
| Scenario | Trigger | Severity | Action | Lead time | Confidence |
|---|---|---|---|---|---|
| Heat + dry spell [HEAT-04] | Tmax >= 38 C for >= 3 d with VPD > 4 kPa: **NAV**, no source; use AEMET levels [S1] as proxy | Medium | Keep SWP above -1.8 MPa | 2-5 d | Low |
| Soil water deficit [FRUITSET-01] | Midday SWP < -1.8 MPa between end of flowering and pit hardening [S3] | Medium | Irrigate | 7 d | Medium |
| Fruit drop risk [FRUITSET-02] | SWP < -2.71 MPa [S3] | High | Rescue irrigation | 3-7 d | Medium |
| Hail [HAIL-01] | AEMET storm warning; yellow = hail > 1 cm, orange = > 2 cm [S1] | High, local | Insurance; copper after hail: **NAV** | 0-1 d | High (trigger) / NAV (action) |
| Olive fly window [FLY-01] | Fruit stone > 10 mm (CLM: > 8-10 mm) [S7, S10]. Install mass-trapping devices Apr-May, 20-50 traps/ha depending on plot size [S6] | Info | Install McPhail + yellow chromotropic traps weekly [S6] | 7 d | High |
| Kaolin [KAOLIN-01] | Apply before summer and before first stings; dose 0.2-5 kg/100 L (highest on first application, lower after), Jun-Sep. Surround WP max 1 application; Argical Pro max 6, PHI 28 d [S6, S10]. Kaolin also cited by the Junta as heat-stress protection [S6]. No source for use on open flowers or for a specific heat trigger: **NAV**. | Low | Apply before first stings | 3-7 d | Medium |
| Prays carpófaga [PRAYS-02] | >= 20% fruits with viable eggs AND 20% of eggs hatched (Málaga Jun 2025: 35.7% fruits with live forms; 56% hatched). Eggs not viable at RH < 30% [S7, S9] | Medium | Intervene per RPI; Chrysoperla can cut egg viability up to 50% [S7] | 7-14 d | High |
| Saissetia oleae [SAIS-01] | Action threshold **NAV**. Population peak in July when mobile nymphs emerge [S11] | Low | Monitor | 1-3 wk | Low |

### 3c. Pit hardening (Jul-Aug)
| Scenario | Trigger | Severity | Action | Lead time | Confidence |
|---|---|---|---|---|---|
| RDI rule [RDI-01] | Table olive: irrigate only when midday SWP < -2.0 MPa. Irrigation by shortfall: < 15% below threshold -> 25% of max ETc (1 mm/d); 15-30% -> 50% (2 mm/d); > 30% -> 100% (4 mm/d); max orchard ETc 4 mm/d [S4] | Opportunity | Apply the 25/50/100% rule | 7-14 d | Medium (one orchard, Manzanilla, pre-harvest restriction; pit hardening-specific % for oil olives NAV) |
| Control target [RDI-02] | SWP >= -1.4 MPa after massive pit hardening [S4, S5] | Info | Full irrigation target | 7-14 d | Medium |
| Severe RDI [RDI-03] | SWP -3.5 MPa: yield unaffected but fruit drop and size related to stress [S5] | High (table olive) | Avoid for table olive | 7-14 d | Medium |
| Kc [KC-01] | FAO-56 olive Kc mid 0.70 (ini 0.65, end 0.70), 40-60% cover [S13] (pit-hardening and regional Kc: **NAV**) | Info | ETc = Kc x ETo | n/a | Medium |
| Extreme heat + drought [EXTREME-01] | Tmax >= 40 C (AEMET orange in 38-C zones [S1]) and SWP < -2.0 MPa [S4]; heat duration **NAV** | High | Suspend RDI, rescue irrigation per RDI-01 (up to 100% max ETc); kaolin per section 3b; avoid pruning | 2-5 d | Medium |
| Hot dry wind [WIND-02] | **NAV** | Medium | NAV | 1-3 d | Low |
| Fly heat suppression [FLY-02/03] | Tmax > 36 C with low RH limits all stages [S7]; CLM: > 30 C lowers egg/young larva viability, > 35 C raises pupal mortality, > 40 C kills adults, optimum 20-25 C [S10] | Info | Hot inland zones lower risk; cooler/humid zones stay at risk | 3-7 d | High (Andalucía/CLM bulletins) |
| Fly action, Andalucía PI [FLY-04/05] | Table olive 1st application: > 1 adult/McPhail/day AND > 50% fertile females. Mill olive 1st application: > 1 adult/trap/day AND > 60% fertile females AND first sting. Follow-up: > 1 adult/trap/d + > 60% fertile females + > 2-3% fruits with live forms, or > 3 adults/trap/d + > 2-3% live forms [S6] | High | Bait-spot (parcheo) on ~25% of farm [S6] | 3-7 d | High |
| Fly action, GIP / CLM [FLY-06/07] | Patch: mill 1 adult/McPhail/d (5/chromotropic/d) + 1% punctured; table first sting. Full tree: 5% punctured (mill) or 1% (table) [S6]. CLM: patch at > 1%, full spray at 5-7% punctured [S10] | High | Patch or full-tree per level | 3-7 d | High |
| Fly, C. Valenciana [FLY-08] | Numeric threshold **NAV**; advisory logic (bait as population rises, repeat every 20 d, full-tree 3-6 d after stings) from search summary only [S15] | Medium | See [S15] | 3-6 d | Low |
| Fly, Cataluña [FLY-09] | > 5% punctured olives (local 2014 advisory, snippet-only) [S16]; IRTA/DOGC PI norm not found | Medium | Local advisory | 3-6 d | Low |
| Fly, Extremadura | **NAV**. Searched DOE 2010 PI order, DOE campaign resolutions 2016/2018/2020 (official campaigns exist; no thresholds read) | | Use Andalucía/CLM values as proxy, flagged | | Low |
| Saissetia heat mortality [SAIS-02] | T > 30 C with RH < 30% gives > 80% first-instar mortality [S11] | Info | If threshold exceeded, treat late July to early August when eggs have hatched [S11] | 1-3 wk | Medium |
| Verticillium [VERT-02] | Soil >= 28 C: disease parameters fall [S12] | Info | No curative control sourced (**NAV**) | season | Medium |
| Xylella vectors [XYL-02] | Adults off olive until autumn [S17, not re-read] | Low | NAV | | Low |
| Hail [HAIL-02] | As HAIL-01 | High, local | Copper: **NAV** | 0-1 d | High (trigger) |

## 4. Variables required per trigger
| Trigger | Variables | Resolution | Forecast horizon |
|---|---|---|---|
| Heat | Tmax 2 m, zone Meteoalerta level | Daily | 1-7 d |
| Hot dry wind | 10 m wind, RH, T | Hourly | 1-3 d |
| Water deficit / RDI | ET0, Kc, rain, irrigation, midday SWP (field, weekly) or soil moisture proxy | Daily; SWP weekly | 7-14 d |
| Hail | AEMET storm/hail warnings | Event | 0-24 h |
| Olive fly | Tmax, RH, McPhail/chromotropic counts, % fertile females, % punctured | Daily; weekly traps | 1-14 d |
| Prays | % inflorescences with live forms, inflorescences/shoot, % fertile flowers, % fruits with viable eggs | Weekly | 1-2 wk |
| Saissetia | T, RH, crawler counts | Daily | 1-3 wk |
| Verticillium | Soil T 0-20 cm | Daily | seasonal |
| Phenology | GDD base 9.1 C [S14]; BBCH | Daily | n/a |

## 5. Notes and limits
- Values with high confidence are official regional/MAPA/AEMET thresholds (fly, Prays, heat alert levels). Agronomic trial values (SWP, RDI) come from single-region trials (Sevilla table olive; Central Spain Arbequina hedgerow) and need local validation.
- Flowering heat thresholds are the weakest block: only in-vitro data [S2]. The earlier draft's S1 (IOC) and S2 (Croatian) numbers were not reproduced: the IOC node had no numbers; the Croatian paper reported only snippet-level results (30 C fully suppressed fruit set in 'Manzanillo' chamber study; 25 C best), not read in full, so not used.
- Not found / blocked: Extremadura PI technical norm thresholds; IRTA/Generalitat PI norm; GVA PI olive norm (DOGV); Andalucía's new PI olive regulation is still in draft (2026) and the old 1997 annexes were not read; MAPA GIP olive guide (2014) not retrieved; Saissetia action threshold; Prays thresholds for CLM/Cataluña/C. Valenciana (Andalucía values used); hot-dry-wind and bloom-rain thresholds; kaolin on open flowers; copper after hail; Verticillium curative actions; olive-specific pit hardening Kc and %ETc for oil olive.
- Draft values dropped as unsourced: hot-wind 8 m/s and RH < 30%, VPD > 4 kPa, 40 C Saissetia crawler mortality, "2 flies/trap/day or 10% punctured", kaolin 3-6%, RDI 25-50% ETc "common practice", Tmin < 0 C frost.

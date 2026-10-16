# Olive scenarios 03: fruit growth -> harvest -> post-harvest/pruning

Scope: Andalucía, Castilla-La Mancha, Extremadura, Cataluña, Comunitat Valenciana.
Status: DEEP PASS (2026-10-16). Sources below were fetched and read (PDF text extracted or page fetched), unless marked "snippet only". Machine-readable triggers: `csv/03_fruit_growth_to_harvest.csv` (42 rows, scenario_ids `OLV-S08-*` fruit growth, `OLV-S09-*` ripening/harvest, `OLV-S10-*` post-harvest). All rows `validated=false`: no agronomist sign-off yet. Confidence = evidence strength (H/M/L). NAV = needs agronomist validation (no source found).

Fixes versus the shallow draft
- Stage 2 frost row: the muddled action ("Harvest immediately after frost? No: ...") is split into a forecast row (prevent: advance harvest of exposed plots) and a post-event row (inspect fruit, segregate and mill frost-affected fruit separately). The "24-48 h after mild frost" window had no source and is now NAV.
- Frost rows now separate lab from field evidence (section 2). The -3 C/12 h figure is a post-harvest freezer test on harvested Arbequina in Chile (reference row only, never a field alert). The field-observational range for autumn drupes is -0.4 to -3 C (review, setting unspecified); AEMET warning levels are a third, human-impact scale.
- Unverifiable draft claims removed: "10% punctured fruit economic damage [S1]" (not found in the cited papers; Andalucía PI/GIP uses 5% oil and 1% table; Giacalone cites 15% as the Mediterranean action level), degree-day bounds 9.5/30 C, and "eggs die at 35-37.8 C" (not re-verified). The irrigation "86-100% ETc" was ET0 in the Chilean model and only for phenols under simulated frost.

## 1. Stage calendar (approximate)

| Stage | South (Jaén/Córdoba/Sevilla/Granada, S. Badajoz) | Inland/cold (CLM, N. Extremadura, Lleida) | Coastal/east (Valencia, Tarragona) |
|---|---|---|---|
| S08 Fruit growth/oil accumulation | to Oct. RAIF Málaga 14-18 Oct 2024: 79% of plots at veraison I1, 19% I2 | NAV | NAV |
| S09 Ripening + harvest | RAIF advises mill harvest advanced to Oct-Nov to limit fly damage | NAV | NAV |
| S10 Post-harvest/pruning | Prune debris must be gone by 1 May (Andalucía rule) | NAV | NAV |

Phenology windows per region are NAV beyond the RAIF observation (no regional phenology table retrieved).

## 2. Evidence separation: frost

| Evidence | Value | Setting | Use |
|---|---|---|---|
| Field-observational (review, setting not specified) | Autumn drop -0.4 to -3 C before harvest: wilting, brown blisters, internal browning, some fully frozen drupes, reduced oil accumulation | Review of field reports | Trigger OLV-S08-FROST-01 / S09-FROST-01,02 |
| Field-observational | 0 to -3 C slight damage to young organs; -6 to -7 C moderate; below -12 to -18 C severe | Review | OLV-S10-PRUNE-02 |
| Lab only | Harvested Arbequina fruit at -3 +/- 1 C for 12 h, thawed 2-4 h: lower phenols and ORAC, "frostbitten" defect low intensity, C6 alcohols down, hexanal +34% (June) | Chile, post-harvest freezer, one orchard/cultivar; authors warn natural frost may differ | Reference row OLV-S08-FROST-02 only |
| Lab LT50 | Leaves -12 C, buds -8 C, twig -16 C, roots -6 C | Controlled freezing | Not a trigger |
| Regulatory | AEMET Tmin yellow/orange/red -4/-8/-12 C (interior), -1/-4/-8 (Campiña, coast), -6/-10/-14 (Cuenca, interior norte Valencia, Castellón interior) | Human-impact warnings | OLV-S08-FROST-03 (escalation) |

Operational consequence: AEMET warnings (-4 C) are colder than the field drupe injury onset (-0.4 C); alerts based on AEMET alone would miss injury. Duration of exposure for field fruit injury is not stated in the source: NAV.

## 3. Scenario -> action tables (sourced values only; ids in CSV)

Sources: [A] AEMET, [F] RAIF fly strategy, [M] RAIF Málaga, [G] Giacalone, [P] Petruccelli, [L] Chile lab, [Mo] Moral, [V] Viruega, [C] Crop Prot., [U] UC IPM, [S] Spilocaea ecology, [K] CLM bulletin, [R] Cyprus RDI. URLs in Sources.

### S08: fruit growth / oil accumulation (Sep - Oct)

| Id | Trigger | Sev. | Action | Lead | Conf. |
|---|---|---|---|---|---|
| FLY-01 | Dusk temp >= 16 C (with RH > 40% and hardened pit) enables oviposition [G] | M | Weekly traps + fruit sampling | 7 d | M |
| FLY-02 | Tmax > 30 C with RH 20-40% = summer diapause (lowers risk) [G]; autumn cooling/RH rise ends it, CLM 2025 flights rose from mid-Sept [K] | L | Expect autumn rebound | 7 d | M |
| FLY-03 | Andalucía PI, oil: first application > 1 adult/McPhail/day + > 60% fertile females + first stung fruit; later > 2-3% live forms [F] | H | Bait/patch treatment (~25% of grove) | 3 d | H |
| FLY-04 | Andalucía GIP oil: whole-tree larvicide at 5% stung (later 5% new); patch at 1 adult/McPhail + 1% stung [F] | H | Larvicide with PHI check | 3 d | H |
| FLY-05 | Andalucía GIP table olive: 1% stung [F] | H | Larvicide / patch | 3 d | H |
| FLY-06 | PI pyrethroids only on autumn generation, before 31 Oct; max 2 deltamethrin sprays [F] | M | Schedule vs PHI | 3 d | H |
| FLY-07 | CLM: peak captures mid-late Oct; Toledo McPhail 24.07/day, N. Cuenca 35.7% viable stung (2025) [K]. No CLM treatment threshold found | M | Follow ERAA/OCA/ASV data | NAV | M |
| HEAT-01 | AEMET Tmax yellow >= 38 C (36 in La Mancha albaceteña, Alcarria, Valencia/Cataluña interior) [A]. Crop damage level NAV | M | Full ETc irrigation where possible | 2 d | M |
| DEFIC-01 | Floor 35% ETc at pit hardening/oil accumulation gave same yield/oil quality as 70% sustained (Cyprus, Koroneiki, low density) [R]. Spanish validation NAV | M | Protect oil-accumulation supply >= 35% ETc | NAV | L |
| RAIN-01..06 | 12 h yellow/orange: 40/80 mm inland (red 120); 60/100 mm coast-prelitoral (red 180). 1 h orange 30 inland, 40 coast (red 60/90) [A] | M-H | Drainage, culverts, no traffic on wet soil | 48 h (1 h: 6 h) | H |
| WIND-01 | Gust yellow >= 70 km/h (orange 90, red 130; 80/100/140 Serranía de Cuenca) [A]. Fruit-drop effect NAV | L | Harvest exposed plots first | 24 h | M |
| HAIL-01/02 | AEMET strong storm: hail > 1 cm (yellow); very strong > 2 cm (orange) [A]; wounds are knot entry points [U]. % damaged fruit for early harvest NAV | H | Document for Agroseguro; copper on wounds promptly (the "24 h" figure is from a secondary guide, low confidence) | 0-24 h | M / L |
| FROST-01 | Tmin <= -0.4 C autumn (field-observational) [P] | H | Harvest exposed plots first; sample fruit | 48 h | M |
| FROST-02 | Lab: -3 C/12 h [L] | n/a | Reference only | n/a | L |
| FROST-03 | AEMET Tmin yellow <= -4 C interior [A] | M | Escalate FROST-01 | 48 h | M |
| ANTH-01 | Anthracnose infection 10-25 C, optimum ~17-20 C, severity rises with wetness to 48 h [Mo] | M | Early harvest of susceptible cultivars | 72 h | M |
| ANTH-02 | Free acidity < 0.8% only if incidence <= 13% (Arbequina, severity < 1.5) or <= 50% (Frantoio, severity < 2) [C] | H | Early harvest, segregate | 72 h | M |
| REP-01 | Peacock spot 8-24 C, optimum 20 C, RH ~100% [M]; lab 5-25 C, max ~20 C with 12-24 h wetness (snippet only: APS page returned 403) [V] | M | Preventive treatment when favourable | 72 h | M |
| REP-02 | PI numeric leaf-infection trigger: NAV (Reglamento text not retrieved) | M | Sample visible + incubated spots | NAV | L |

### S09: ripening + harvest (Oct - Dec)

| Id | Trigger | Sev. | Action | Lead | Conf. |
|---|---|---|---|---|---|
| FROST-01 | Tmin forecast <= -0.4 C [P] | H | Advance harvest of exposed plots, mill promptly. Irrigation/potassium mitigation is lab-modelled only [L] | 48 h | M |
| FROST-02 | Tmin <= -0.4 C occurred [P] | H | Cut-test fruit, harvest and mill affected fruit as a separate lot; hours-to-harvest NAV | NAV | L |
| RAIN-01 | 12 h orange >= 80 mm inland / 100 mm coast [A] | H | Harvest ripe plots first; no traffic on saturated soil | 48 h | H |
| RAIN-02 | Dry spell / soil moisture needed for shaker harvest: NAV (searched PI/RAIF/CLM/trade; trade note says 2-3 dry days, unverified) | M | Re-sequence plots | NAV | L |
| WIND-01 | Gust >= 70 km/h [A] | L | Harvest exposed plots first | 24 h | M |
| FLY-01 | > 15% infested fruit = Mediterranean action level [G]; RAIF: advance mill harvest to Oct-Nov [F] | H | Advance harvest, segregate | 72 h | M |
| FLY-02 | Post-harvest tillage under canopy cuts overwintering pupae [F] | L | Till where compatible | 7 d | M |
| ANTH-01/02 | Arbequina > 13% incidence [C]; 10-25 C wetness up to 48 h [Mo] | H / M | Early, fast harvest; segregate | 72 h | M |
| REP-01 | Spilocaea spore density peaks Nov-Feb, zero in summer; rain-splash dispersal [S] | M | Plan post-harvest protection | 7 d | M |
| DEFIC-01 | Pre-harvest irrigation: NAV | L | None without local validation | NAV | L |

### S10: post-harvest / recovery / pruning

| Id | Trigger | Sev. | Action | Lead | Conf. |
|---|---|---|---|---|---|
| PRUNE-01 | Pruning wounds stay susceptible to olive knot >= 14 days; leaf scars ~7 d; spread by rain; dry-summer wounds not susceptible [U] (California; Spanish duration NAV) | M | Prune with 14 d dry outlook; sanitise tools (10% bleach); copper per label | 72 h | M |
| PRUNE-02 | Tmin <= -6 C = moderate damage [P]; AEMET -4/-8/-12 [A]. Pruning-delay rule is general practice, NAV | M | Delay pruning in cold interior zones until damage visible | 72 h | M |
| PRUNE-03 | No pruning debris in field from 1 May (Phloeotribus); seal large cuts where history of damage [M] (Andalucía rule) | M | Remove or store wood | 7 d | H |
| REP-01 | 8-24 C, optimum 20 C [M]; aerating pruning, limit N, resistant cvs Lechín de Sevilla, Manzanilla de Hellín, Picudo de Montoro [Rep] | M | Aerating prune, protective fungicide if justified; copper dose/timing NAV | 72 h | M |
| WLOG-01 | Waterlogging after DANA: not searched, NAV | H | Drain, no traffic | NAV | L |
| DRY-01 | Dry autumn: NAV | M | None | NAV | L |

## 4. Variables and temporal resolution

| Trigger | Variables | Resolution | Horizon |
|---|---|---|---|
| Frost | Hourly Tmin (2 m), hours below threshold (duration not defined by source: NAV) | Hourly | 72 h |
| Rain/DANA | 1 h and 12 h accumulations (match AEMET), soil moisture | Hourly | 24-96 h |
| Hail | Radar, CAPE, AEMET storm warnings (hail > 1 / > 2 cm) | 15 min - 6 h | 0-48 h |
| Heat/wind | Tmax, hourly gusts (AEMET levels) | Hourly | 7-10 d |
| Olive fly | Trap counts, % fertile females, % stung / live forms, dusk T, RH | Weekly traps, hourly weather | 7 d |
| Anthracnose / peacock spot | Hourly T, RH, leaf wetness hours (proxy: rain or RH > 90%) | Hourly | 3-7 d |
| Pruning | Rain in 14 d after cut | Daily | 14 d |

`action_lead_time_h` values in the CSV are system design assumptions, not source values, except where the source states a date (31 Oct, 1 May).

## 5. Gaps (NAV) and what was searched

- Regional PI olive texts for Castilla-La Mancha, Extremadura, Cataluña (IRTA/DARP) and Comunitat Valenciana (GVA/IVIA): searched "producción integrada olivar" per region, DOCM/DOE/DOGV/DOGC. Retrieved: Extremadura Order 23-Dec-2003 and 29-Jun-2010 (framework only, no numeric thresholds; the 2003 PDF is the fly campaign order), CLM Feb 2026 fly bulletin (monitoring data, no threshold). Not found: any CLM or Valencia olive PI order, Catalan olive PI standard. Direct fetches of the CLM boletines nº 6/16/18/20/22 and of the GVA fly notice (9-Sep-2025) and a Tarragona notice failed (404, connection refused). A Tarragona notice with a 5% stung-fruit trigger and a Valencian bait-treatment notice were seen only as search snippets, not read: leads, not used.
- So all numeric fly PI thresholds apply to Andalucía only; other regions are NAV for fly/peacock-spot PI triggers. MAPA national IPM olive guide PDF not retrieved.
- Andalucía PI Reglamento (autumn peacock-spot leaf-infection %, copper dose): not retrieved; a 2026 draft Order for a new Reglamento exists (Junta de Andalucía MAIN document, regulatory memo, no thresholds read).
- AEMET: thresholds are from Meteoalerta ANX1 v1 (31-May-2022); a later plan version (v9, Jan 2025) exists and was not checked for changed thresholds. Warnings are impact levels, not crop-damage thresholds.
- Not found: field duration of autumn fruit frost injury; cultivar-specific field fruit-freeze temperature; shaker-harvest dry-spell rule; waterlogging/Phytophthora; Spanish RDI floors; olive hail fruit-loss %; heat or wind fruit-drop thresholds; IOC guide figures (no IOC document fetched in this pass).

## Sources (fetched unless noted)
- [A] AEMET Meteoalerta ANX1 Umbrales y niveles de aviso v1: https://web2.aemet.es/documentos/es/eltiempo/prediccion/avisos/plan_meteoalerta/METEOALERTA_ANX1_Umbrales_y_niveles_de_aviso.pdf
- [F] Junta de Andalucía, Estrategias de manejo de la mosca del olivo, campaña 2024: https://www.juntadeandalucia.es/agriculturapescaaguaydesarrollorural/raif/wp-content/uploads/2023/09/ESTRATEGIA-DE-MANEJO-DE-LA-MOSCA-DEL-OLIVO.pdf
- [M] RAIF olivar Málaga 14-18 Oct 2024: https://www.juntadeandalucia.es/agriculturapescaaguaydesarrollorural/raif/wp-content/uploads/2024/10/Informe_Fitosanitario_1014_1020-6.pdf
- [Rep] RAIF Recomendaciones repilo (GIP olivar): https://www.juntadeandalucia.es/agriculturapescaaguaydesarrollorural/raif/wp-content/uploads/2023/04/Recomendaciones-para-el-Repilo-31-03-2023.pdf
- [K] Castilla-La Mancha boletín fitosanitario nº1 feb 2026 (mosca): https://agricultura.castillalamancha.es/sites/default/files/2026-03/BOLETIN%20N1_ENE26.pdf
- [G] Giacalone et al., Olive fruit fly in South Africa: https://iris.unipa.it/bitstream/10447/218502/1/Giacalone%20et%20al%2015%20Olive%20Fruit%20Fly%20in%20South%20Africa.pdf
- [P] Petruccelli et al. 2022, cold stress in Olea europaea (Plants): https://pmc.ncbi.nlm.nih.gov/articles/PMC9144808/
- [L] Light frost, irrigation and potassium, Arbequina oil (Chile lab): https://pmc.ncbi.nlm.nih.gov/articles/PMC11117877/
- [Mo] Moral et al. 2012, Phytopathology (crossref abstract): https://doi.org/10.1094/PHYTO-12-11-0343
- [V] Viruega et al. 2011, Plant Disease 95(9):1139 (search-snippet abstract only; page 403): https://apsnet.org/publications/plantdisease/2011/September/Pages/95_9_1139.aspx
- [S] Spilocaea oleagina survival, inoculum and dispersal, Plant Dis. 2013 (crossref abstract): https://doi.org/10.1094/PDIS-12-12-1206-RE
- [C] Anthracnose acceptable for EVOO, Crop Protection 108:47-53, 2018 (AGRIS abstract): https://agris.fao.org/search/fr/records/65deee62b766d82b18ff33fc
- [U] UC IPM Olive knot: https://ccfruitandnuts.ucanr.edu/sites/default/files/2011-03/78742.pdf ; secondary (24 h copper claim, snippet only): https://wikifarmer.com/library/en/article/olive-knot-disease-guide
- [R] Siakou et al. 2021, deficit irrigation Koroneiki Cyprus (AGRIS): https://agris.fao.org/search/es/records/65dec15b0f3e94b9e5d10367
- Extremadura framework: https://doe.juntaex.es/pdfs/doe/2010/1300O/10050229.pdf ; https://doe.juntaex.es/pdfs/doe/2003/740o/03050360.pdf

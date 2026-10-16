# Ground-truth and proxy-label datasets for the Kairos olive decision table

Research date: 2026-10-16. Scope: Andalucia (ES-AN), Castilla-La Mancha (ES-CM), Extremadura (ES-EX), Cataluna (ES-CT), Comunitat Valenciana (ES-VC).

Problem: `configs/crops/olive/decision_table.csv` has 143 rows, all `validated=false`, and the team has no calibration data. Thresholds come from lab and field papers (Frontiers 2024, De Melo-Abreu 2004, Hueso 2021, GIP guide, AEMET Meteoalerta). This note lists open or free-registration datasets that can serve as ground truth or proxy labels, with a realistic plan.

Verification legend, applied per item:
- **VERIFIED** = URL resolved (HTTP 200) or an API call returned data in this session, and I read the metadata or content.
- **PARTIAL** = the page or file loaded but a detail (licence, coverage) comes from a search snippet or general knowledge.
- **UNVERIFIED** = could not reach or confirm. Do not rely on it without checking.

Note on method: some hosts (ismn.bafg.de, ismn.earth, www.siar.es, ivia.es, agroseguro.es PDFs) timed out, refused or returned 403 to `curl` from this sandbox. That does not mean they are down for you.

---

## 0. Executive ranking (hackathon, a few days)

| Rank | Dataset | Why | Rows it can test | Effort |
|---|---|---|---|---|
| 1 | **SIAR daily/hourly weather (MAPA), via API** | Free after registration. 500+ stations, hourly (30 min), daily and monthly Tmin/Tmax/RH/rain/radiation/ET0/soil temp. Covers the olive belt in all 5 regions. This is the weather side of every back-test. | All `climate`-class rows (FROST, CHILL, HEAT, PHEN, RAIN, REPILO leaf-wetness proxy via RH, FLY-02/03 heat suppression) | 1 day |
| 2 | **RAIF Andalucia olive end-of-campaign and weekly reports (PDF)** | The only open source of field-observation labels: % leaves with repilo, % punctured fruit, McPhail captures, Prays infested inflorescences, phenology by province and biological zone, 2022-2025. | REPILO-DEC-01, PRAYS-ANT-01, FLY-04..09, PHEN-01..04 timing, S01-REPILO-* | 2 days (PDF scraping) |
| 3 | **MAPA "Superficies y producciones anuales" (olivar) + ESYRCE + Eurostat `apro_cpshr`** | Province-level and NUTS2 olive area, yield (t/ha), production, oil yield per year. Yield-anomaly proxy label for bad years (frost, heat at bloom, drought). | FROST-*, HEAT-*, DROUGHT-*, EXTREME-01 (year-level) | 1 day |
| 4 | **Agroseguro claims reports (PDF) + ENESA** | Only open record of insured loss events by crop (olivar), CCAA and risk (sequia, viento, helada, pedrisco). Coarse but real damage labels. | HAIL-*, WIND-*, DROUGHT-*, FROST-* (year x CCAA only) | 1 day, low resolution |
| 5 | **Zenodo olive yield + Sentinel-2 dataset, Cordoba 2017-2023** (record 18891490) and **PLOS ONE Jaen yield data** (record 11102805) | Parcel-level olive yield with NDVI and agroclimatic variables. CC-BY. Directly usable to fit a yield-vs-stress model. | HEAT, DROUGHT, CHILL (parcel-year), PHEN | 1-2 days |

Honorable mentions: Meteocat XEMA via Socrata (easiest API for Cataluna), AEMET OpenData daily climatology (station network for all regions), HR-VPP phenology (satellite flowering/senescence timing), Copernicus C3S/ESA CCI soil moisture.

Realistic hackathon plan: SIAR plus AEMET weather, joined to RAIF phenology and pest percentages and to MAPA/Eurostat provincial yield and Agroseguro loss years. Do an event-study back-test ("did rows X fire in years/places where yield or claims were anomalous?"). Do not promise per-parcel validated thresholds. Anything at a stem-water-potential (SWP) level (DROUGHT-01/02, FRUITSET-*, RDI-*) cannot be validated with open Spanish data. See section 7.

---

## 1. Olive phenology observations

### 1.1 RAIF Andalucia "Informe de Especial Interes Olivar" and weekly "Informe Fitosanitario"
- **URL (VERIFIED, HTTP 200):** https://www.juntadeandalucia.es/agriculturapescaaguaydesarrollorural/raif/ (portal). Example end-of-campaign report: https://www.juntadeandalucia.es/agriculturapescaaguaydesarrollorural/raif/wp-content/uploads/2026/01/Informe_EspecialInteres_Olivar_2025.pdf. Balance report: https://www.juntadeandalucia.es/agriculturapescaaguaydesarrollorural/raif/wp-content/uploads/2025/11/Balance_Informe_EspecialInteres_Olivar-2024.pdf. Weekly example: https://www.juntadeandalucia.es/agriculturapescaaguaydesarrollorural/raif/wp-content/uploads/2025/06/Informe_Fitosanitario_0428_0504-4.pdf
- **Provider:** Junta de Andalucia (Consejeria de Agricultura), RAIF network.
- **Measures:** Olive phenology by province and biological zone (first inflorescences, flowering start/end, letter stages C, D, F, H plus BBCH in some reports), inflorescences per shoot, % fertile flowers, Prays attack, repilo, olive fly. Text and tables in PDF.
- **Coverage:** Andalucia only, province and biological zone level. Annual reports found for 2022, 2023, 2023-24, 2024, 2025. Weekly bulletins found from 2022 onward in search results.
- **Format:** PDF (no CSV/API found). I read the 2025 PDF text with `pdftotext`. It contains province-level % leaves with visible repilo and olive-fly sections.
- **Licence:** Not stated on the files I opened. Junta de Andalucia open-data default is CC BY 4.0, but **UNVERIFIED** for these PDFs. Cite RAIF.
- **Access:** Direct download, no registration. Needs scraping/regex or manual transcription.
- **Validates:** `OLV-S03-PHEN-01..04` (GDD to full flowering vs real flowering dates; compute GDD from SIAR and compare), `OLV-S03-PRAYS-ANT-01/02`, `OLV-S01-REPILO-DEC-01`, `OLV-S02-REPILO-DEC-01`, `OLV-S05-PRAYS-01`.
- **Rank:** very high for this project.

### 1.2 AEMET phenological network
- **URL:** AEMET OpenData https://opendata.aemet.es/centrodedescargas/inicio (VERIFIED 200; API key request button; licence text: use and reproduction allowed citing AEMET as author). A 2019 AEMET talk describing the network is at https://repositorio.aemet.es/bitstream/20.500.11765/10426/1/05_Romero_Fenologia_2019.pdf (VERIFIED 200).
- **Measures:** Phenological observations (olive flowering among them), according to secondary sources. Moving to BBCH coding. Feeds PEP725.
- **Coverage / access:** I could **not** find or verify a public bulk download or API endpoint for the phenology records. The OpenData landing page did not list a phenology dataset, and my guess at a phenology page URL returned 404. **UNVERIFIED that olive phenology data is downloadable.** Practical route: email AEMET's climate service, or request via PEP725 (below).
- **Licence:** AEMET attribution licence (above).
- **Validates (if obtained):** PHEN-01..04, CHILL-01..08.

### 1.3 PEP725 Pan-European Phenology Database
- **URL:** https://www.pep725.eu/ (VERIFIED 200, redirects to https://pep725.eu/). Page https://www.pep725.eu/data_download.php returned 404.
- **Provider:** ZAMG/GeoSphere Austria with EUMETNET. Roughly 12 million records, about 265 species/cultivars (per an EGU abstract); BBCH based.
- **Access:** Free registration and acceptance of the data policy, then filtered download. Research use only.
- **Whether olive (Olea europaea) is in the species list: UNVERIFIED.** Search found nothing mentioning it. Olive is at the edge of the temperate network, so expect sparse or no coverage. Check the species filter after registering. Do not plan around it.
- **Validates:** PHEN-*, if present.

### 1.4 Aerobiology (olive pollen) as flowering-date proxy
- **Idea:** Olive pollen season start/peak from aerobiology networks (Red Espanola de Aerobiologia, Red de Aerobiologia de Andalucia, Catalan XAC) is a strong objective flowering marker and was used in the Spanish phenology literature (Garcia-Mozo, Oteros, Galan 2015, 10 sites in Cordoba 1996-2012, BBCH).
- **URL (PARTIAL):** https://www.uco.es/rea resolved (HTTP 200) but I did not confirm a data download. Access terms **UNVERIFIED**.
- **Validates:** PHEN-*, HEAT-01..03 (flowering heat), FROST-inflorescence.

### 1.5 Published phenology time series
- Garcia-Mozo et al. 2015 (Ann Agric Environ Med) and Oteros et al. (agris.fao.org record 675982e8c7a957febdf9e75d, found by search; not opened) give Cordoba flowering dates by year. Use the numbers in the paper tables if the raw data is not shared. **PARTIAL.**

---

## 2. Olive yield and production statistics

### 2.1 MAPA "Superficies y producciones anuales de cultivos" (olivar sheet)
- **URL (VERIFIED):** page https://www.mapa.gob.es/es/estadistica/temas/estadisticas-agrarias/agricultura/superficies-producciones-anuales-cultivos/ ; olive file https://www.mapa.gob.es/dam/mapa/contenido/estadisticas/temas/estadisticas-agrarias/2.agricultura/3.-superficies-y-producciones-anuales/reglamento-n--543-2009/re1_olivar_formato_tabla_global.xlsx (HTTP 200, xlsx, about 52 MB) and `...-0.xlsx` (about 1 MB, the lighter one).
- **Provider:** MAPA, Subdirección General de Análisis, Coordinación y Estadística.
- **Measures:** Area, yield, production and destination of olive (table olive, oil olive, oil yield) by CCAA and province (NUTS2 and NUTS3), from the olive "TABLA GLOBAL" sheets. The page says the 2025 provisional and 2024 provisional files are available, and links older Anuarios from 1999 on.
- **Format:** xlsx with a dropdown in cell B1. The page says to select the crop there.
- **Licence:** MAPA open reuse of public-sector information (Spanish Ley 37/2007). Exact licence text **not read**. PARTIAL.
- **Access:** Direct download.
- **Municipality level:** The page links "IME - Estadisticas de superficies de cultivos por terminos municipales" (PDF, VERIFIED 200). It describes the municipal statistics (area), not production. Municipal olive production is not published nationally. Andalucia's aforo (olive crop forecast) is municipal in the regional IECA stats, but I could not verify a URL (https://www.juntadeandalucia.es/institutodeestadisticaycartografia/aoliva/ gave 404). **UNVERIFIED.**
- **Validates (year x province proxy label):** FROST-01..03, S03-FROST-*, S03-HEAT-*, S05-HEAT-*, DROUGHT-*, EXTREME-01, RDI rows. Use yield anomaly versus 5-year trend (olive alternate bearing must be detrended).

### 2.2 ESYRCE (MAPA, area survey)
- **URL (VERIFIED, 200):** https://www.mapa.gob.es/es/estadistica/temas/estadisticas-agrarias/agricultura/esyrce/ . Files include `312distribuciondefrutalesolivaryvinedodemesasegun...2023.xlsx` (olive by variety, planting density, age) and `311_estimaciones_de_rendimientos_de_los_principales_cultivos_2023.xls` (yield estimates; HTTP 200). Years 2022, 2023, 2024 (advance) found. A "tendencias mensuales rendimientos cultivos" page also resolved.
- **Measures:** Land use, crop areas (sampling-based), olive varieties/age/density, irrigation typology. Not yield per parcel.
- **Format:** xlsx/xls. Microdata description docx on the page.
- **Use:** Weighting rainfed vs irrigated, variety mix by province (cultivar-specific CHILL/FROST thresholds).

### 2.3 Eurostat `apro_cpshr` (crop production, NUTS2)
- **URL (VERIFIED by API call):** https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/apro_cpshr?format=JSON&lang=EN&geo=ES61&crops=O1000&sinceTimePeriod=2015 . Dataset title "Crop production in EU standard humidity by NUTS 2 region", updated 2026-09-08. Crop code `O1000` = Olives. Indicators: area, harvested production, yield (t/ha). My sample call for ES61 returned values for the 2015-2024 period (area series seen; check production/yield codes `HPRD_HUMD_EU_THS_T`, `YLD_HUMD_EU_T_HA` yourself because values for some indicators/regions may be missing).
- **NUTS2 codes needed:** ES61 Andalucia, ES42 Castilla-La Mancha, ES43 Extremadura, ES51 Cataluna, ES52 Comunitat Valenciana.
- **Licence:** Eurostat reuse policy (CC BY 4.0 equivalent). Access: free JSON/SDMX API, no key. Annual only.
- **Use:** Cross-check of MAPA numbers and region-level yield time series. National level `tag00122` also exists.

### 2.4 AICA (olive oil declarations)
- **URL (VERIFIED 200):** https://www.aica.gob.es . The page links the "SIMO" online service (`/servicios-en-linea/simo`) and "Informes". I did not open SIMO.
- **Measures:** Monthly olive oil production in mills, stocks, by province (province figures appear in press reports of AICA data, e.g. Jaen 164,841 t, Cordoba 120,559 t, Sevilla 85,388 t to 31-Dec-2025). Data format on the AICA site **UNVERIFIED**; secondary press coverage (interempresas.net) reproduces monthly values.
- **Use:** Monthly in-season production (accumulating from October) per province. Gives the "bad campaign" label earlier than annual statistics. Good for a campaign-level check of DROUGHT and heat rows.

---

## 3. Pest and disease monitoring

### 3.1 RAIF Andalucia reports (same sources as 1.1)
- Content verified in 2025 end-of-campaign PDF: sections for "MOSCA DEL OLIVO (Bactrocera oleae)" and "REPILO (Fusicladium oleagineum)" with province-level % visible repilo (e.g. 1.30% at start of campaign versus 0.90% previous; zone means 2.40, 1.60, 1.50%).
- Search results show weekly Malaga bulletins with: McPhail captures per trap per day (e.g. 10 flies/trap/day in Nov 2022), pheromone panel captures (0.6 and 4.4 adults/trap/day in summer 2022), % punctured olives (4.5% Oct 2024), and the sentence that fly activity falls above 36 C.
- **Format:** PDF only. **No machine-readable trap data found** on the open-data portal.
- **Validates:** `OLV-S05-FLY-02/03` (heat suppression at 36 and 30 C: compare weekly capture curves against SIAR Tmax in the same province), `OLV-S05-FLY-04..09`, `OLV-S08-FLY-*`, `OLV-S09-FLY-01`, REPILO-DEC-01 (1% leaves).
- A 2.5-day scraper for 2022-2025 bulletins gives ~100+ weekly province-level points per pest.

### 3.2 GBIF occurrences
- **URL (VERIFIED by API):** https://api.gbif.org/v1/occurrence/search?scientificName=Bactrocera%20oleae&country=ES&limit=0 returned **356** Spanish occurrence records. *Prays oleae* in Spain: **42**. *Olea europaea* in Spain: 170,238 (mostly iNaturalist/herbarium).
- **Licence:** per record, CC0 / CC BY / CC BY-NC. **Access:** free API/bulk (bulk download needs a free GBIF account).
- **Assessment:** Presence points only, no absences or abundance. Not useful for threshold calibration. Marginal, low priority.

### 3.3 iNaturalist
- API call returned 57 research-grade-agnostic observations of *B. oleae* in a place query (place_id 6753, which I assumed is Spain; **PARTIAL**). Same limits as GBIF. Low priority.

### 3.4 Olive fly trap time series from the literature
- Zenodo record 15568571 (VERIFIED via API): "Spatiotemporal Dynamics of Olive Fruit Fly Populations ... Eight-Year Study from Samos [Greece]", files `Traps Samos 2017-2024.xlsx`, `Samos Temp-Hours.xlsx`, CC BY 4.0, open. **Greece, not Spain**, but it is the only open weekly trap + temperature series found. Can test `OLV-S05-FLY-02/03` and `OLV-S08-FLY-01/02` temperature suppression logic in a different climate. Mark as an out-of-region sanity check only.

### 3.5 Other regional bulletins
- Cataluna (DACC/ADV bulletins), Valencia (Sanidad Vegetal), CLM and Extremadura: **UNVERIFIED**. I did not find open datasets. Treat as manual/PDF at best.

---

## 4. Heat / frost / drought damage records

### 4.1 Agroseguro (insured losses)
- **URLs:** https://agroseguro.es/sala-de-prensa/informe-de-siniestralidad/eventos-mas-significativos-por-cultivos/ (VERIFIED via WebFetch; olive section lists drought and wind events with hectares and euros by CCAA for 2023: 82,194 ha affected, about EUR 36.41M, Andalucia 32.34M, CLM 1.46M, Extremadura 1.78M). Year-end report PDF: https://agroseguro.es/wp-content/uploads/2024/02/TOTAL-SINIESTRALIDADES-2023_31-diciembre-2023.pdf (PDF, 18 pages; text compressed, I could not extract details; direct curl returns 403 so use a browser). Andalucia 2025 press note (found by search): https://agroseguro.es/wp-content/uploads/2026/02/NP-Agroseguro_Siniestralidad-seguro-agrario-Andalucia.pdf (search snippet: Andalucia claims EUR 63.4M, olive EUR 6.8M; curl 403, **PARTIAL**).
- **Measures:** Insured losses by crop, cause and CCAA (not province or municipality in what I saw).
- **Format:** PDF and web text. **No open CSV/API found.** Agroseguro's main site `www.agroseguro.es` timed out from the sandbox (and `/agroseguro/estadisticas` gave 200 via WebFetch, but it did not list olive tables I could confirm).
- **Licence:** None stated. Treat as citable public information, not redistributable bulk data.
- **ENESA:** https://www.mapa.gob.es/es/enesa/ (VERIFIED 200). "Informes de contratacion" PDFs (e.g. https://www.mapa.gob.es/dam/mapa/contenido/enesa/090_publicaciones/informes-de-contratacion/documentos/ic18_def.pdf, found by search) give insured area and capital by crop and CCAA. Olive insurance uptake is low (national average under 10% per ASAJA statement), so claims under-represent damage, especially in CLM.
- **Validates:** Year x CCAA: HAIL-*, WIND-*, DROUGHT (2023: strong drought year), EXTREME-01. Frost for olive claims: not found; the olive text mentions only drought, wind and "other climate adversities".
- **Rank:** useful for a handful of labelled years, not for threshold fitting.

### 4.2 Consorcio de Compensacion de Seguros
- https://www.consorciodecompensacion.es timed out from the sandbox. Its relevant data are extraordinary-risk losses on property, not crops. **UNVERIFIED and probably irrelevant.**

### 4.3 JRC
- JRC MARS Bulletin (publications repository, e.g. https://publications.jrc.ec.europa.eu/repository/handle/JRC124835 found by search, not opened) reports monthly crop conditions and cold or heat events, including the January 2021 cold spell in Iberia. Text only, no olive damage dataset. **PARTIAL.**
- European/Global Drought Observatory (https://drought.emergency.copernicus.eu VERIFIED 200): soil-moisture anomaly, SPI, fAPAR anomaly maps and downloadable products, free. Use as a drought proxy label (soil moisture anomaly, fAPAR anomaly) for DROUGHT-01 (winter dry) and OLV-S10-DRY-01. Data format and licence **PARTIAL** (Copernicus open licence).

### 4.4 News-based event list (manual)
- Olive Oil Times articles on specific frost and hail events (e.g. El Comtat freeze 2010, Monterrubio de la Serena hail) can serve as a handful of named events (found by search). Anecdotal. Use for a sanity check on FROST-01..03 and HAIL-* only.

---

## 5. In-situ weather and soil-moisture networks

### 5.1 SIAR (MAPA agroclimatic network for irrigation)
- **URL (VERIFIED, 200):** https://servicio.mapa.gob.es/siarweb/ ; API technical manual https://servicio.mapa.gob.es/siarweb/documentos/manuales/ManualTecnico_WEB_API_SIAR.pdf (VERIFIED, read); "Datos publicados" https://servicio.mapa.gob.es/siarweb/documentos/masInfo/Datos-Publicados.pdf (VERIFIED, read). API base per manual: `https://servicio.mapa.gob.es/siarapi/API/V1/`. The older name `www.siar.es` timed out.
- **Provider:** MAPA, with regional partners (Andalucia IFAPA, CLM, Extremadura, Valencia, Cataluna stations are part of the national SiAR; exact list per region **UNVERIFIED**, check the station list through the API).
- **Measures:** 30-min data: mean T, RH, wind speed/direction, solar radiation, rain, soil temperature at 10 and 30 cm. Daily: Tmean/max/min with times, RH mean/max/min, wind, radiation, rain, ET0. Weekly and monthly aggregates derived from daily. Times in UTC since 1 April 2014.
- **Coverage:** More than 500 stations (MAPA press release, 19-Oct-2023, VERIFIED by reading the PDF). History length varies per station; many start in the early 2000s, **UNVERIFIED**.
- **Format:** JSON through API; web downloads (xls/csv) from the portal.
- **Licence:** Not stated in what I read. **UNVERIFIED.** Free after registration; request limits per day and per minute are emailed to you.
- **Access:** Register on the SiAR site ("Mi SiAR"), tick API registration in "Editar perfil", then obtain a token (per the technical manual; an older manual describes a 50-character API key, so use the current technical manual). Budget a day for registration lag.
- **Validates:** FROST-*, CHILL-*, CHILL-REV-*, PHEN GDD, HEAT-*, RAIN, REPILO (RH >= 98% proxy; no leaf wetness sensor in the daily file), FLY-02/03, `OLV-S05-VERT-01/02` (soil temp 10 and 30 cm is near but not equal to the 0-20 cm layer), KC-01 (via ET0).
- **Rank:** top for weather.

### 5.2 AEMET OpenData
- **URL (VERIFIED 200):** https://opendata.aemet.es/dist/index.html (API Swagger) and the download centre above. Free API key by email request.
- **Measures:** Daily climatology (Tmax/Tmin/rain etc.) and recent hourly observations for AEMET stations; also warnings.
- **Licence:** use and reproduction allowed citing AEMET (footer text read).
- **Access:** API key; rate-limited; fetching long histories station by station is slow.
- **Validates:** WARN-COLD-*, AEMET-Y38/O40/R44 rows (these rows are AEMET warning levels, so you can test how often the zone-level rule fires versus station Tmax), and the same list as SIAR.
- Best use: second source for cross-checking SIAR and for reference stations in Jaen, Cordoba, Badajoz, Toledo, etc.

### 5.3 Meteocat (Cataluna) XEMA via Socrata
- **URLs (VERIFIED, API returned data):** https://analisi.transparenciacatalunya.cat/resource/7bvh-jvq2.json (daily XEMA data from the start of measurements, e.g. station VK Raimat from 1988-09-01) and https://analisi.transparenciacatalunya.cat/resource/nzvn-apee.json (XEMA 30-min data). The metadata says licence "See Terms of Use"; Meteocat's open-data terms are CC BY 4.0, **PARTIAL (not read here)**.
- **Format:** JSON/CSV via Socrata SODA, no key needed for small queries (app token advisable).
- **Note:** Meteocat's own API (https://api.meteo.cat) returned 403 without a key; the Socrata mirror is easier.
- **Validates:** all climate rows for ES-CT (Lleida, Tarragona; Arbequina region, relevant to CHILL-01 and PHEN-01 which were calibrated partly at Reus).

### 5.4 Regional networks other than SIAR
- **Junta de Andalucia RIA (IFAPA):** https://www.juntadeandalucia.es/agriculturaypesca/ifapa/riaweb/web/ (VERIFIED 200). A community R package (`meteospain`) shows the RIA web service supports daily and monthly data by station and province. Official API documentation **not found**, some monthly endpoints gave 404. PARTIAL.
- **Valencia IVIA agroclimatic network, Castilla-La Mancha (ITAP/regional SiAR), Extremadura (CICYTEX/regional network):** sites (`ivia.es`, `itap.es`) timed out; no public bulk download confirmed. **UNVERIFIED.** The stations in these regions that feed SiAR are the practical route.
- **Inforiego (Castilla y Leon):** https://www.inforiego.org (200). Outside the five target regions, but it hosts REMEDHUS-adjacent soil moisture. Not needed.

### 5.5 ISMN soil-moisture stations
- **URL:** https://ismn.earth (portal; **timed out from the sandbox, UNVERIFIED directly**). Search results show the portal at ismn.bafg.de with "Data Download" and "Terms and Conditions" pages.
- **Terms (from a search snippet, PARTIAL):** free registration required to download; scientific use only; no redistribution; cite ISMN and each network; no commercial use. Check this against your use (a hackathon demo is fine, a product is not).
- **Spain:** REMEDHUS (22 stations, Duero basin, Castilla y Leon, updated to 2024 per an ISMN news note) and a Castilla y Leon Inforiego soil moisture set. **Neither is in an olive area.** No olive-grove ISMN stations found. Limited value for olive rules; useful only to sanity check ERA5-Land or CCI soil moisture error in Spain.
- **Validates:** none directly. Skip for the hackathon.

---

## 6. Remote-sensing proxies

### 6.1 Copernicus HR-VPP (Seasonal Trajectories, VPP parameters)
- **URL (VERIFIED, 200):** https://land.copernicus.eu/api/en/products/vegetation/high-resolution-season-length (HR-VPP season-length resource); access through WEkEO https://wekeo.copernicus.eu (200). Common product page paths I guessed returned 404, so navigate from the CLMS site.
- **Measures:** Plant Phenology Index time series at 10 m, 10-day steps, plus 13 phenology parameters (start/peak/end of season, season length, etc.) per year from 2017, EEA38 + UK.
- **Format:** GeoTIFF; Sentinel Hub also lists it as open data.
- **Licence:** Copernicus land products: "full, open and free access" with attribution (EEA catalogue text via search; **PARTIAL**).
- **Caution:** Evergreen olive has weak seasonality in vegetation indices; start-of-season is a poor proxy for flowering. Better as a stress/greenness anomaly label (low peak PPI in drought year).
- **Validates:** drought rows at the year/parcel level (greenness anomaly), not flowering rows.

### 6.2 Sentinel-2 NDVI with parcel datasets (ready-made)
- **Zenodo 18891490:** Soil, climate and Sentinel-2 NDVI for olive yield, Cordoba, 2017-2023 (VERIFIED via Zenodo API; CC BY 4.0; open; files `olive_growers_all_data.xlsx` 0.9 MB and README).
- **Zenodo 11102805:** PLOS ONE (Jaen) yield data with Landsat 7/8 indices, 2009-2022 (VERIFIED via API; CC BY 4.0; files `Raw_Data_Olive_Crop_Yield_JAEN.xlsx`, `JAEN_L7&L8_INDICES_09_22.xlsx`, error-prediction sheets). Paper: https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0311530
- **Zenodo 14017071 and 14017108:** Extremadura olive enclosure (48,500 plots, CSV about 1.9 GB) and Sentinel-2 mean-value parcel characterisation for 2021-22 (CSV about 0.5 GB), CC BY 4.0 (VERIFIED via API). No yield labels.
- **Zenodo 7233908:** olive stress ground-truth vs Sentinel-2, Halkidiki, Greece (CC BY 4.0, CSV 109 KB; VERIFIED). Out of region; visual/lab stress scores, useful for a generic NDVI-stress sanity check.

### 6.3 Soil moisture
- **C3S satellite soil moisture (ESA CCI merged):** https://cds.climate.copernicus.eu/datasets/satellite-soil-moisture (VERIFIED 200; CDS account, free; ~0.25 degree, daily, 1978-present). ESA project page: https://climate.esa.int/en/projects/soil-moisture/ (200). Resolution is coarse relative to groves.
- **Use:** Test OLV-S10-DRY-01 / S01-DROUGHT-01 style rules (water-year anomalies), and `root_zone_available_water` NAV rows in a proxy form.

### 6.4 ECOSTRESS
- https://lpdaac.usgs.gov/products/eco2lstev002/ (VERIFIED 200). Land surface temperature and ET products at ~70 m, irregular revisit, NASA Earthdata free registration. Heavy to process; low priority for a few-day project. Would help a canopy-temperature heat-stress proxy for HEAT-04 / EXTREME-01. Skip unless a team member has experience.

### 6.5 Land cover / olive grove masks
- **CORINE Land Cover** (class 223 olive groves): https://land.copernicus.eu/en/products/corine-land-cover (VERIFIED 200), free. Use to mask station and satellite pixels.
- **SIGPAC / regional crop maps:** MAPA IDE download page returned 404 for my guessed path; **UNVERIFIED.** The Zenodo Extremadura enclosure set (above) already provides olive parcel geometries for that region.

### 6.6 Drought indices
- SPEI database (CSIC): https://spei.csic.es (VERIFIED 200). Gridded monthly SPEI for Spain, free. Easy drought-year labels for provincial averages.

---

## 7. Stem water potential, sap flow and flux data

This is the weakest category. The decision table's DROUGHT-*, FRUITSET-*, and RDI-* rows depend on midday stem water potential (SWP), which no national network measures.

| Dataset | Verified? | Notes |
|---|---|---|
| **Universidad de Sevilla (idUS) dataset "Managing Water Stress in Olive Orchards Using Reference Equations for Midday Stem Water Potential"**, DOI 10.12795/11441/148243 | DOI resolves (HTTP 200), landing page at https://idus.us.es/handle/11441/148243 mentions the title; **file format and licence not read** (page is JavaScript-rendered) | Seville, Manzanilla de Sevilla hedgerow, 3 seasons 2020-2022, 3 irrigation treatments, SWP. Best Spanish SWP data found. Links to Shackel et al. 2021 baseline (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8663634/, VERIFIED 200). Could test SWP thresholds (-1.2, -1.4 MPa) against irrigation treatment and yield, for one orchard. |
| Zenodo 14563519, olive hydromulch in pots, SWP | search hit only; potted trees, CC BY 4.0 | Not field-representative. |
| Zenodo 11299406, C-band radar + sap flow + SWP-related data, irrigated olive, Morocco | VERIFIED via API but **access restricted**, no files visible | Request-only; out of region. |
| Hueso et al. 2021, Agric. Water Manag. 248 (Central Spain, Arbequina hedgerow) | Paper page 403 to curl; table values cited in decision table | Source for DROUGHT-01/02 thresholds. No public data found. |
| Eddy-covariance olive sites (Jaen, Univ. Granada/CSIC; e.g. https://digital.csic.es/handle/10261/345135 VERIFIED 200) | Landing page only | Published, not in FLUXNET/ICOS as far as I could find. The code `ES-ES1` from the brief **could not be confirmed** as an olive site (search found nothing; I believe ES-ES1 is El Saler, a pine forest, **UNVERIFIED**). FLUXNET data page https://fluxnet.org/data/fluxnet2015-dataset/ resolved (200). |
| ICOS Carbon Portal https://data.icos-cp.eu | VERIFIED 200 | No olive site identified. |

Conclusion: do not claim validation of SWP-based rows. You may calibrate a "soil-water or ET0-minus-rain proxy for SWP" only with the Seville dataset.

---

## 8. Mapping to decision table prefixes

| Prefix | Best open validation data | Strength | Notes |
|---|---|---|---|
| FROST (S01-FROST-01..04, S02-FROST-*, S03-FROST-*, S08-FROST-*, S09-FROST-*, S10-PRUNE-02) | SIAR + AEMET + Meteocat Tmin; MAPA/Eurostat yield anomaly; news events | Weak-moderate | Frost damage is rare. Tmin at 2 m is not canopy temperature. No open frost-damage inventory for olive. |
| WARN-COLD-*, AEMET-Y38/Y36/O40/O39/R44/R42 | AEMET OpenData warnings + station data | Strong (internal consistency) | Tests the rule against official warnings, not crop damage. |
| CHILL / CHILL-REV | SIAR hourly T (need 30-min or hourly data, Oct to Jan) + RAIF flowering dates + Zenodo Cordoba data | Moderate | Need hourly T for chill-unit model; SIAR provides 30-min. |
| PHEN (GDD) | SIAR + RAIF flowering dates (Cordoba, Sevilla, Jaen) + Garcia-Mozo 2015 | Strong-moderate | Best calibration target. RMSE vs 2-3 days claimed by De Melo-Abreu. |
| HEAT (S03-HEAT-01, S05-HEAT-01..03, S02-HEAT-01, S05-HEAT-04, S08-HEAT-01) | SIAR Tmax + MAPA/Eurostat yield + Zenodo Cordoba/Jaen yields | Moderate | In vitro pollen thresholds; yield is year-level and confounded. |
| FLY (S05-FLY-*, S08-FLY-*, S09-FLY-*) | RAIF weekly/annual PDFs (captures, % punctured fruit) + SIAR Tmax | Moderate | Only Andalucia. Greek Zenodo series as out-of-region check. |
| REPILO | RAIF % visible leaves (start/end of campaign) + SIAR RH/rain/Tmean | Moderate | SIAR lacks leaf-wetness; use RH >= 98% hours or rain as proxy. |
| PRAYS | RAIF Prays reports | Moderate-weak | PDF values only. |
| DROUGHT (S01-DROUGHT-01, S10-DRY-01, S02-DROUGHT-02 etc.) | SIAR rain + ET0; SPEI; JRC GDO soil moisture; Agroseguro 2023 drought; yield anomaly | Moderate for dry year/winter rows | SWP rows not testable. |
| RDI, FRUITSET, KC | None open at scale (Seville dataset only) | Very weak | Literature values only. |
| RAIN-* | SIAR/AEMET 12 h rain (use hourly data) versus AEMET warnings | Internal consistency only | Waterlogging threshold NAV, no labels. |
| HAIL, WIND | Agroseguro claim years; AEMET warnings | Weak | Event-level, no hail dataset found. |
| VERT, XYL, ANTH, SAIS | None found | None | Skip. |

---

## 9. Recommended hackathon workplan (3 to 4 days)

1. **Day 0:** Register for SIAR (token delays), AEMET OpenData key and Copernicus CDS account. Download the MAPA olive xlsx, the Eurostat JSON, and the three Zenodo records (18891490, 11102805, 15568571).
2. **Day 1:** Pull SIAR daily and 30-min data for 20 to 40 olive-belt stations (Jaen, Cordoba, Sevilla, Ciudad Real/Toledo, Badajoz, Tarragona/Lleida, Valencia/Alicante), 2010 to 2025. Compute the decision-table triggers (FROST, HEAT, CHILL, GDD) per station-year.
3. **Day 2:** Scrape RAIF PDFs (2022-2025 end-of-campaign plus weekly) into a table of dates and % values. Compare GDD-to-flowering predictions and repilo/fly thresholds with observed values.
4. **Day 3:** Event-study: for each province-year compute trigger counts and compare with yield anomaly (MAPA/Eurostat) and Agroseguro loss years (2023 drought, others). Report hit rate and false alarm rate per row family; state clearly that this is plausibility testing, not calibration.
5. **Output honesty:** keep `validated=false` in the CSV. Add a column or note "proxy-checked against X" instead of marking true.

## 10. Items I could not verify

- PEP725 holding olive records; AEMET phenology bulk download.
- Licence text of RAIF PDFs, SiAR, MAPA xlsx (assumed open reuse of public information).
- Whether SiAR includes IVIA, CLM and CICYTEX stations in the API (likely, check station list) and per-station history length.
- ISMN site (unreachable from sandbox) and the claim that no olive stations exist there.
- Agroseguro PDF contents beyond web text (403 for curl, compressed text through the fetch tool); provincial detail unlikely.
- Aerobiology network data access (uco.es/rea reachable, no data link checked).
- Municipal-level olive production source (IECA aforo) and SIGPAC download URL.
- iNaturalist `place_id` for Spain; Eurostat production/yield values for ES61, ES42, ES43, ES51, ES52 (only ES61 area test call).
- Meteocat Socrata licence wording (shown as "See Terms of Use").
- ES-ES1 being an olive site: probably not.
- Consorcio de Compensacion de Seguros data (site unreachable; likely not crop-relevant).

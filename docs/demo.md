# Demo: farmer app, advisor app, advisor dashboard

One command runs everything: `make demo-up` (prints the iPhone URLs on your Wi-Fi).

| Surface | URL | What it is |
|---|---|---|
| Farmer app (iPhone) | `/farmer/` | Alerts, advice detail, "Ask Elena to check this", Report a problem, Parcels, Advisor chat |
| Advisor app (iPhone) | `/advisor/` | Your farmers, requests, field reports, validate / edit / hold-off |
| Advisor dashboard (desktop) | `http://localhost:8501` (Streamlit, `demo/dashboard_app.py`) | Satellite map of the LPIS plots, rule-engine actions per plot, weather time series per plot, validation, batch validate |
| Agronomist scenario review | `http://localhost:5050` (Flask, `agronomist/app.py`) | Plain-language list of the 142 decision-table scenarios; approve, change or reject each; decisions apply live and export to CSV |
| API | `/docs` | `/demo/*` endpoints shared by all three; state in `data/processed/demo/state.json` |

The three share one state store, so a request sent in the farmer app appears in the advisor app and dashboard within seconds, and a validation comes back to the farmer as "Checked by advisor". The replay date lives in the shared state (Me tab in either app, or the date box on the dashboard).

## Real vs demo
- **Real:** plot shapes, areas, SIGPAC references, slope, altitude and irrigation coefficient from LPIS; ERA5-Land weather per plot cell (2025); weather alerts from the decision table via `rules/table_engine.py`.
- **Kairos rules not in the table:** soil drying and rain ahead (`configs/crops/olive/water_rules.yaml`). They are relative to each cell's own year, low confidence, and need agronomist calibration.
- **Demo data:** grower, farm and plot names, varieties (unless an external dataset is joined), the irrigation log and water-use alert, seeded requests and reports.
- **Replay:** "tomorrow" and "forecast" are the actual following days of 2025. There is no live forecast yet.
- Advice is rule-based. The apps call it "Kairos advice", not AI advice.

## Build the data
`uv run python scripts/build_demo_farms.py` reads `data/raw/lpis` and the 2025 ERA5 files and writes `data/processed/demo/{farms.json,cell_features.csv.gz}`.

To join an olive dataset, drop CSVs in `data/raw/olive_dataset/` with a `sigpac_ref` column (`province:municipality:aggregate:zone:polygon:parcel:enclosure`) plus any of `variety, irrigation, planting_year, tree_density, yield_kg_ha`, then re-run the script.

## Agronomist review
Reviews are saved in `data/processed/agronomist/reviews.json` and read by the rule engine (`rules/reviews.py`). Approve marks a scenario `validated`, "approve with changes" replaces its threshold and advice, reject stops it firing, "field check" keeps it unvalidated. The three apps pick the change up within seconds. "Download CSV" exports the table with each decision, reviewer and comment. The literature table itself (`decision_table.csv`) is never edited.

### Interactive figures (crop level, not per plot)
Each weather-testable scenario page has live figures over the whole crop area (province series weighted by the crop's area): a season chart with a draggable threshold and RAIF field reports where they exist, a sensitivity curve (threshold vs. how many warnings), and a month × province heatmap. "Use in my decision" copies the chosen threshold into the review form. The **Crop overview** page shows the stage calendar, a scenario × month firing heatmap (click a row to open it), review progress and lists of scenarios that never fire or fire most. The header's crop menu lists every crop with a decision table; only olive has weather series so far. Figures load Plotly from a CDN (internet needed).

## AI assistant (RAG, Ollama)
Farmer app → alert → "Ask Kairos about this alert". `src/kairos/assist/` retrieves decision-table rows (hazard filter + BM25), asks a local model (`ollama pull qwen2.5:3b`, override with `KAIROS_LLM`), rejects answers containing numbers not in the retrieved rules, and falls back to the standard advice if Ollama is down. The rule engine alone decides what fires.

**Advisor feedback:** in the Streamlit dashboard, the **AI answers** tab lists each answer with Good / Save my correction / Bad. Verdicts go to `data/processed/assist/feedback.jsonl`; good and corrected answers are fed back as examples for the same hazard, bad ones are never reused. `feedback.export_sft(path)` writes a fine-tuning set. `uv run python scripts/eval_assist.py` runs the golden questions.

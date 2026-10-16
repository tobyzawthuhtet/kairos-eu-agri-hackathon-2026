# Kairos — Farm-Level Extreme Weather Alerts & Advisories (Team 20)

EU Agri Hackathon 2026 · Team *Compost Compilers* / Kairos

Starting with **olive** (Spain), we fuse on-ground sensors, satellite observations, weather
stations and empirical crop models into farm-level, crop-specific alerts (heat waves, drought,
weather-driven pests/diseases), cross-validated by agronomists and delivered via a web app.

## Pipeline
ingest → align to farm → bias-correct (vs sensors) → olive models → decision rules → alert → agronomist review → farmer web app

See [docs/architecture.md](docs/architecture.md), [docs/data-sources.md](docs/data-sources.md), [docs/decision-rules.md](docs/decision-rules.md).

## Layout
- `src/kairos/` — ingestion, fusion, models, rules, alerts, api
- `configs/` — crop thresholds (`crops/olive.yaml`) and regions; crop-agnostic by design
- `web/` — React + Vite + TypeScript app
- `data/` — raw/interim/processed (contents gitignored)
- `infra/` — Docker (placeholder)

## Quickstart
```
cp .env.example .env
make install
make test
make api    # http://localhost:8000/health
make web    # http://localhost:5173
```

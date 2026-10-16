# Architecture
1. **Ingestion** (`kairos.ingestion`): one `Source` subclass per data source (sensors, satellite, weather stations, downscaled climate).
2. **Fusion** (`kairos.fusion`): spatial/temporal alignment to farm-daily records; bias-correction of model outputs against sensors.
3. **Models** (`kairos.models`): empirical olive stress-response (heat, drought, pest/disease) -> `RiskAssessment`.
4. **Rules** (`kairos.rules`): risk -> concrete action (irrigate / protect trees) -> `Alert`.
5. **Review** (`kairos.alerts.review`): agronomist approval keeps a human link.
6. **API + Web** (`kairos.api`, `web/`): farmers see approved alerts and advisories.

Status: scaffold. Storage, deployment and data download pending team decisions.

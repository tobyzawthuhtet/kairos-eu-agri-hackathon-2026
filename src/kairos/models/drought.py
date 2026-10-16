"""Empirical olive drought-stress model (soil moisture + NDVI anomaly)."""
from kairos.schemas import DailyObservation, Hazard, RiskAssessment, Severity


def assess_drought(history: list[DailyObservation], cfg: dict) -> RiskAssessment | None:
    d = cfg["drought"]
    last = history[-1]
    low_sm = last.soil_moisture is not None and last.soil_moisture < d["soil_moisture_low"]
    ndvi_drop = (
        last.ndvi is not None and last.ndvi_baseline
        and 100 * (last.ndvi_baseline - last.ndvi) / last.ndvi_baseline >= d["ndvi_drop_pct"]
    )
    if not (low_sm or ndvi_drop):
        return None
    both = low_sm and ndvi_drop
    return RiskAssessment(
        farm_id=last.farm_id, hazard=Hazard.drought,
        severity=Severity.high if both else Severity.moderate, score=0.8 if both else 0.5,
        rationale=f"low soil moisture={bool(low_sm)}, NDVI drop={bool(ndvi_drop)}",
    )

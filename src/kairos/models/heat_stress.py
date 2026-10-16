"""Empirical olive heat-stress model."""
from kairos.schemas import DailyObservation, Hazard, RiskAssessment, Severity


def assess_heat(history: list[DailyObservation], cfg: dict) -> RiskAssessment | None:
    """history: most recent days, oldest first, for a single farm."""
    h = cfg["heat"]
    streak = 0
    for o in reversed(history):
        if o.tmax_c is not None and o.tmax_c >= h["tmax_stress_c"]:
            streak += 1
        else:
            break
    if streak == 0:
        return None
    peak = max(o.tmax_c for o in history[-streak:])
    severe = peak >= h["tmax_severe_c"]
    if streak >= h["consecutive_days"] and severe:
        sev = Severity.severe
    elif streak >= h["consecutive_days"]:
        sev = Severity.high
    else:
        sev = Severity.moderate
    score = min(1.0, streak / (2 * h["consecutive_days"]) + (0.3 if severe else 0))
    return RiskAssessment(
        farm_id=history[-1].farm_id, hazard=Hazard.heat, severity=sev, score=score,
        rationale=f"{streak} consecutive day(s) with Tmax >= {h['tmax_stress_c']}C, peak {peak}C",
    )

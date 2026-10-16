"""Run models + rules for a farm and produce pending alerts."""
from kairos.config import load_crop
from kairos.models.drought import assess_drought
from kairos.models.heat_stress import assess_heat
from kairos.rules.engine import apply_rules
from kairos.rules.olive_rules import OLIVE_RULES
from kairos.schemas import Alert, DailyObservation


def generate_alerts(history: list[DailyObservation], crop: str = "olive") -> list[Alert]:
    cfg = load_crop(crop)
    risks = [r for r in (assess_heat(history, cfg), assess_drought(history, cfg)) if r]
    return apply_rules(risks, OLIVE_RULES)

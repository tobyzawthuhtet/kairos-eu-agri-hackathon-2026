"""Olive-specific rules. Placeholders pending agronomist validation."""
from kairos.schemas import Hazard, RiskAssessment, Severity


def heat_rule(r: RiskAssessment):
    if r.hazard is Hazard.heat and r.severity in (Severity.high, Severity.severe):
        return ("Heat wave risk", "Irrigate early morning/evening; avoid midday work; consider shade or kaolin spray.")
    return None


def drought_rule(r: RiskAssessment):
    if r.hazard is Hazard.drought:
        return ("Drought stress detected", "Irrigate within 48h; prioritize fruit-set/pit-hardening stages.")
    return None


OLIVE_RULES = [heat_rule, drought_rule]

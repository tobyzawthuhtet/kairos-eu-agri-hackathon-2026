"""Weather-driven pest/disease risk (olive fly, peacock spot). TODO: implement from config."""
from kairos.schemas import DailyObservation, RiskAssessment


def assess_pest_disease(history: list[DailyObservation], cfg: dict) -> list[RiskAssessment]:
    return []

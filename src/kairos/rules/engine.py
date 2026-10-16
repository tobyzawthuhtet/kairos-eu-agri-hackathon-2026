"""Decision-rule engine: RiskAssessment -> Alert with a concrete action."""
from collections.abc import Callable
from datetime import UTC, datetime

from kairos.schemas import Alert, RiskAssessment

Rule = Callable[[RiskAssessment], tuple[str, str] | None]  # -> (title, action)


def apply_rules(risks: list[RiskAssessment], rules: list[Rule]) -> list[Alert]:
    alerts = []
    for r in risks:
        for rule in rules:
            out = rule(r)
            if out:
                title, action = out
                alerts.append(Alert(
                    farm_id=r.farm_id, hazard=r.hazard, severity=r.severity, title=title,
                    action=action, created_at=datetime.now(UTC),
                ))
                break
    return alerts

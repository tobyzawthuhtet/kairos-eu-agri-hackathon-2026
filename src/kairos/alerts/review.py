"""Agronomist review queue: alerts are approved before reaching farmers. TODO: persistence."""
from kairos.schemas import Alert


def approve(alert: Alert, agronomist: str) -> Alert:
    return alert.model_copy(update={"reviewed_by": agronomist, "approved": True})

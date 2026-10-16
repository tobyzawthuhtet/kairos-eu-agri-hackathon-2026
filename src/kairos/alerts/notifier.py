"""Deliver approved alerts (web push / email / SMS). TODO."""
from kairos.schemas import Alert


def notify(alert: Alert) -> None:
    raise NotImplementedError

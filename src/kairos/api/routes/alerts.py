from fastapi import APIRouter

from kairos.serving import replay

router = APIRouter()


@router.get("")
def list_alerts(date: str | None = None, province: str | None = None, severity: str | None = None) -> list[dict]:
    return replay.alerts(date, province, severity)

from datetime import date

from fastapi import APIRouter, HTTPException

from kairos.serving import replay

router = APIRouter()


def _check(d: str) -> None:
    try:
        date.fromisoformat(d)
    except ValueError:
        raise HTTPException(422, "date must be YYYY-MM-DD") from None


@router.get("/meta")
def meta() -> dict:
    return replay.meta()


@router.get("/provinces")
def provinces() -> list[dict]:
    return replay.provinces()


@router.get("/replay/{province}")
def day(province: str, date: str) -> dict:
    _check(date)
    out = replay.day(province, date)
    if out is None:
        raise HTTPException(404, "unknown province or date outside the replay range")
    return out


@router.get("/observations/{province}")
def observations(province: str, date: str, window_days: int = 21) -> list[dict]:
    _check(date)
    return replay.observations(province, date, window_days)


@router.get("/backtest")
def backtest() -> dict:
    return replay.backtest()


@router.get("/rules/not-evaluable")
def not_evaluable() -> list[dict]:
    return replay.not_evaluable()

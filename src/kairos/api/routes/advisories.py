from fastapi import APIRouter, HTTPException

from kairos.serving import replay

router = APIRouter()


@router.get("/{rule_id}")
def advisory(rule_id: str) -> dict:
    out = replay.advisory(rule_id)
    if out is None:
        raise HTTPException(404, "rule not found or not evaluable from weather data")
    return out

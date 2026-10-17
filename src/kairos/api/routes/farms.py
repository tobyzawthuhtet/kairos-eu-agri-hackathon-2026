from fastapi import APIRouter

from kairos.serving import replay

router = APIRouter()


@router.get("")
def list_provinces() -> list[dict]:
    """Province-level olive areas (farm-level boundaries come from LPIS in a later step)."""
    return replay.provinces()

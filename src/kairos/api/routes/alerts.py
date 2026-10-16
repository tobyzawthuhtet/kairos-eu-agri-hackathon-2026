from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_items() -> list:
    return []  # TODO: wire to storage

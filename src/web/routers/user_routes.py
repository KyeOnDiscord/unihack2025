import logging

from fastapi import APIRouter

from models.user_models import UserDto

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.get("/{user_id}/")
def get_user(user_id: int) -> dict:
    _log.debug(f"Got user: {user_id}")
    return {"user_id": user_id, "name": "John Doe"}

@router.post("/")
def create_user(user: UserDto) -> dict:
    _log.debug(f"Creating user: {user}")
    return {"message": "User created", "user": user}

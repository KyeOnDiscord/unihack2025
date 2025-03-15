# Handle uploading timetable and anything else related to the timetable here.

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from models.user_models import UserDto
from web.user_auth import get_current_active_user

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/users/preferences",
    tags=["preferences"],
)


@router.post("/")
async def save_preferences(
    current_user: Annotated[UserDto, Depends(get_current_active_user)],
    preferences: str,
) -> dict:
    current_user.preferences = preferences

    return {"message": "Preferences saved"}

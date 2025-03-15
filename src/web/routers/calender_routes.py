# Handle uploading timetable and anything else related to the timetable here.

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from models.user_models import UserDto
from web.user_auth import get_current_active_user

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/users/calender",
    tags=["calender"],
)


@router.post("/")
async def save_calender(
    current_user: Annotated[UserDto, Depends(get_current_active_user)],
    calender_ics_link: str,
) -> dict:
    current_user.calender_ics_link = calender_ics_link

    return {"message": "Calender saved"}

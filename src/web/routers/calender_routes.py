# Handle uploading timetable and anything else related to the timetable here.

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, status

from models.user_models import UserDto
from web.user_auth import get_current_active_user

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/calender",
    tags=["calender"],
)


@router.post("/")
async def upload_calender(
    current_user: Annotated[UserDto, Depends(get_current_active_user)],
    calender_ics: Annotated[bytes, File()],
) -> dict:
    ...

    return {"message": "Calender uploaded"}

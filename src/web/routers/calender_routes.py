# Handle uploading timetable and anything else related to the timetable here.

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

import config
from modules.ical import Calendar
from modules.db import CollectionRef, UserRef
from models.user_models import UserDto
from fastapi import HTTPException, status
from web.user_auth import get_current_active_user, get_user

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
    user_collection = await config.db.get_collection(CollectionRef.USERS)

    current_user.calender_ics_link = calender_ics_link
    await user_collection.update_one(
        {UserRef.ID: current_user.id}, {"$set": current_user.model_dump_safe()}
    )

    return {"message": "Calender saved"}

@router.get("/")
async def get_calender(
    current_user: Annotated[UserDto, Depends(get_current_active_user)],
) -> dict:
    user = await get_user(current_user.id)

    if not user or not user.calender_ics_link:
        return {"events": []}

    calender = Calendar(user.calender_ics_link)
    await calender.fetch_calendar()

    user_calendars = {
        "events": [
            {
                "summary": event.summary,
                "start_time_iso": event.start_time.timestamp(),
                "end_time_iso": event.end_time.timestamp(),
                "duration_seconds": event.duration.seconds,
            }
            for event in calender.events
        ],
    }

    if not user_calendars["events"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found",
        )

    return user_calendars
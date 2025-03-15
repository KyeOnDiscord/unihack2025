# Handle uploading timetable and anything else related to the timetable here.

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, status

from models.user_models import UserDto
from web.user_auth import get_current_active_user

import config
from modules.db import CollectionRef, UserRef

from modules.mail import mail, create_message

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/mail",
    tags=["mail"],
)


@router.post("/mail/send")
async def send_mail(user_id: str):
    user_collection = await config.db.get_collection(CollectionRef.USERS)
    user = await user_collection.find_one({UserRef.ID: user_id})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    else:
        # valid user can send email
        print('a')
        print(user)
        await mail.send_message(
            create_message(
                recipients=[user["email"]],
                subject="Test",
                body="Test",
            )
        )
        return {"message:": "Email sent"}
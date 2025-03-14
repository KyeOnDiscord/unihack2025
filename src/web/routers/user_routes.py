import logging

from fastapi import APIRouter, Depends, HTTPException, status

import config
from models.user_models import UserDto
from modules.db import CollectionRef, UserRef
from web.auth import require_api_key

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/{user_id}/")
async def get_user(user_id: int) -> dict:
    user_collection = await config.db.get_collection(CollectionRef.USERS)
    return await user_collection.find_one({UserRef.ID: user_id})


@router.post("/")
async def register_user(user: UserDto) -> dict:
    user_collection = await config.db.get_collection(CollectionRef.USERS)

    if await user_collection.find_one({UserRef.ID: user.id}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with the same id already exists")
    elif await user_collection.find_one({UserRef.EMAIL: user.email}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with the same email already exists")

    await user_collection.insert_one(user.model_dump())

    _log.info(f"User {user.id} created")

    return {"message": "User created", "user": user}

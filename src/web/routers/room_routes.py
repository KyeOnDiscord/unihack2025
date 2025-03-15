# Handle creating rooms, getting room info, getting room code, getting users to
# join groups by code, etc.
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

import config
from models.room_models import RoomDto
from models.user_models import UserDto
from modules.db import CollectionRef, RoomRef
from web.auth import require_api_key
from web.user_auth import get_current_active_user

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/rooms",
    tags=["rooms"],
    dependencies=[Depends(require_api_key)],
)

MAX_USERS_PER_ROOM = 10


@router.get("{room_id}")
async def get_room(room_id: str) -> dict:
    room_collection = await config.db.get_collection(CollectionRef.ROOMS)
    room = await room_collection.find_one({RoomRef.ID: room_id})
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    else:
        return room


@router.post("/")
async def create_room(
    current_user: Annotated[UserDto, Depends(get_current_active_user)],
    room: RoomDto
) -> dict:
    room_collection = await config.db.get_collection(CollectionRef.ROOMS)
    room.id = str(uuid.uuid4())
    room.users = []
    await room_collection.insert_one(room.model_dump())
    _log.info(f"Room {room.id} created")
    return {"message": "Room created", "room": room, "owner_id": current_user.id}


@router.post("/{room_id}/join")
async def join_room(
    current_user: Annotated[UserDto, Depends(get_current_active_user)],
    room_id: str,
) -> dict:
    room_collection = await config.db.get_collection(CollectionRef.ROOMS)
    room = await room_collection.find_one({RoomRef.ID: room_id})
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    if current_user.id in room.get("users", []):
        return {"message": "User already in room"}
    if len(room.get("users", [])) >= MAX_USERS_PER_ROOM:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is full (max 10 users)",
        )
    await room_collection.update_one(
        {RoomRef.ID: room_id},
        {"$push": {"users": current_user.id}}
    )
    return {"message": "User added to room"}


@router.post("/{room_id}/leave")
async def leave_room(
    current_user: Annotated[UserDto, Depends(get_current_active_user)],
    room_id: str,
) -> dict:
    room_collection = await config.db.get_collection(CollectionRef.ROOMS)
    room = await room_collection.find_one({RoomRef.ID: room_id})
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    if current_user.id not in room.get("users", []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not in room",
        )
    await room_collection.update_one(
        {RoomRef.ID: room_id},
        {"$pull": {"users": current_user.id}}
    )
    return {"message": "User removed from room"}


@router.get("/{room_id}/sync")
async def sync_calendars(room_id: str) -> dict:
    room_collection = await config.db.get_collection(CollectionRef.ROOMS)
    user_collection = await config.db.get_collection(CollectionRef.USERS)
    room = await room_collection.find_one({RoomRef.ID: room_id})
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    user_calendars = []
    for user_id in room.get("users", []):
        user = await user_collection.find_one({"id": user_id}, {"calendar": 1})
        if user and "calender" in user:
            user_calendars.append(user["calendar"])
        return {"message": "Schedules synced", "schedules": user_calendars}

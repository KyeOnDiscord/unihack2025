# Handle creating rooms, getting room info, getting room code, getting users to
# join groups by code, etc.
import asyncio
from datetime import datetime
import logging
import random
import string
import uuid
from typing import Annotated
from groq import Groq

from fastapi import APIRouter, Depends, HTTPException, status, Query

import config
from models.room_models import RoomDto
from models.user_models import UserDto
from modules.db import CollectionRef, RoomRef
from modules.ical import Calendar
from web.user_auth import get_current_active_user, get_user

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/rooms",
    tags=["rooms"],
)

MAX_USERS_PER_ROOM = 10


@router.get("/{room_id}/get")
async def get_room(room_id: str) -> dict:
    room_collection = await config.db.get_collection(CollectionRef.ROOMS)

    room = RoomDto.model_validate(await room_collection.find_one({RoomRef.ID: room_id}))
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    else:
        return room.model_dump()


@router.post("/")
async def create_room(
    current_user: Annotated[UserDto, Depends(get_current_active_user)], room: RoomDto
) -> dict:
    room_collection = await config.db.get_collection(CollectionRef.ROOMS)

    room.id = str(uuid.uuid4())
    room.users = [current_user.id]
    room.owner_id = current_user.id
    room.room_code = "".join(random.choices(string.digits, k=6))
    await room_collection.insert_one(room.model_dump())
    _log.info(f"Room {room.id} created")

    return {"message": "Room created", "room": room.model_dump()}


@router.post("/{room_code}/join")
async def join_room(
    current_user: Annotated[UserDto, Depends(get_current_active_user)],
    room_code: str,
) -> dict:
    room_collection = await config.db.get_collection(CollectionRef.ROOMS)
    room = RoomDto.model_validate(await room_collection.find_one({RoomRef.ROOM_CODE: room_code}))
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    if current_user.id in room.users:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="User already in room")

    if len(room.users) >= MAX_USERS_PER_ROOM:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is full (max 10 users)",
        )
    
    room.users.append(current_user.id)

    await room_collection.update_one(
        {RoomRef.ID: room.id}, {"$push": {"users": current_user.id}}
    )

    return {"message": "User added to room", "room": room.model_dump()}


@router.post("/{room_id}/leave")
async def leave_room(
    current_user: Annotated[UserDto, Depends(get_current_active_user)],
    room_id: str,
) -> dict:
    room_collection = await config.db.get_collection(CollectionRef.ROOMS)

    room = RoomDto.model_validate(await room_collection.find_one({RoomRef.ID: room_id}))
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    elif current_user.id not in room.users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not in room",
        )

    room.users.remove(current_user.id)
    if room.owner_id == current_user.id:
        if len(room.users) > 0:
            room.owner_id = random.choice(room.users)
        else:
            # Delete this room
            await room_collection.delete_one({RoomRef.ID: room_id})

            return {"message": "User left room & room deleted"}

    await room_collection.update_one(
        {RoomRef.ID: room_id}, {"$set": room.model_dump_safe()}
    )

    return {"message": "User removed from room", "room": room.model_dump()}


@router.get("/{room_id}/calenders")
async def get_room_calenders(
    current_user: Annotated[UserDto, Depends(get_current_active_user)], room_id: str
) -> dict:
    room_collection = await config.db.get_collection(CollectionRef.ROOMS)
    room = RoomDto.model_validate(await room_collection.find_one({RoomRef.ID: room_id}))
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    elif current_user.id not in room.users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not in the requested room",
        )

    user_calendars = {}
    users = {}

    async def fetch_user_calender(user_id: str) -> None:
        user = await get_user(user_id)
        users[user.id] = user

        if not user:
            return
        elif not user.calender_ics_link:
            return

        calender = Calendar(user.calender_ics_link)
        if not await calender.fetch_calendar():
            return

        user_calendars[user.id] = {
            "user": user.model_dump(),
            "calender_events": [
                {
                    "summary": event.summary,
                    "start_time_iso": event.start_time.timestamp(),
                    "end_time_iso": event.end_time.timestamp(),
                    "duration_seconds": event.duration.seconds,
                }
                for event in calender.events
            ],
        }

    fetch_tasks = []
    for user_id in room.users:
        fetch_tasks.append(fetch_user_calender(user_id))

    await asyncio.gather(*fetch_tasks)

    start_end_times = []
    for user_id, calender in user_calendars.items():
        for event in calender["calender_events"]:
            start_end_times.append(
                {
                    "user_id": user_id,
                    "type": "start",
                    "time": datetime.fromtimestamp(event["start_time_iso"]),
                }
            )
            start_end_times.append(
                {
                    "user_id": user_id,
                    "type": "end",
                    "time": datetime.fromtimestamp(event["end_time_iso"]),
                }
            )

    start_end_times.sort(key=lambda x: (x["time"], 1 if x["type"] == "start" else 0))

    free_times_by_time = {}
    current_free_users = []
    for start_end in start_end_times:
        if start_end["type"] == "end":
            # User has no class, is free.
            if start_end["user_id"] not in current_free_users:
                current_free_users.append(start_end["user_id"])
        elif start_end["type"] == "start":
            # User has class, no longer free.
            if start_end["user_id"] in current_free_users:
                i = current_free_users.index(start_end["user_id"])
                current_free_users.pop(i)

        free_times_by_time[start_end["time"].timestamp()] = current_free_users.copy()

    free_times_order = sorted(free_times_by_time.keys())

    free_times = []  # Same format as calender_events
    for i, time_ in enumerate(free_times_order[:-1]):
        free_users = free_times_by_time[time_]
        if len(free_users) < 2:
            continue

        start_time = datetime.fromtimestamp(time_)
        end_time = datetime.fromtimestamp(free_times_order[i + 1])
        
        if current_user.id not in free_users:
            continue

        if start_time.day != end_time.day:
            continue

        free_times.append(
            {
                "summary": "Free time",
                "start_time_iso": start_time,
                "end_time_iso": end_time,
                "duration_seconds": (start_time - end_time).seconds,
                "free_users": {
                    user_id: users[user_id]
                    for user_id in free_users
                },
            }
        )

    return {
        "message": "Schedules synced",
        "room": room.model_dump(),
        "schedules": user_calendars,
        "free_times": free_times,
    }


@router.get("/my-rooms")
async def get_user_rooms(
    current_user: Annotated[UserDto, Depends(get_current_active_user)],
) -> dict:
    room_collection = await config.db.get_collection(CollectionRef.ROOMS)
    rooms = []
    async for room in room_collection.find({"users": current_user.id}):
        rooms.append(room)
    return {"message": "User rooms fetched", "rooms": rooms}


@router.get("/preference")
async def get_common_interests(
    user_ids: Annotated[list[str], Query(..., alias="user_ids")], 
    event_time: Annotated[str, Query(..., alias="event_time")]
) -> dict:
    user_interests = {}
    users = {}

    async def fetch_user_preferences(user_id: str) -> None:
        user = await get_user(user_id)
        if not user:
            return
        users[user.id] = user
        if user and user.preferences:
            user_interests[user.id] = user.preferences
    
    fetch_tasks = [fetch_user_preferences(user_id) for user_id in user_ids]
    await asyncio.gather(*fetch_tasks)

    all_interests = [interests for interests in user_interests.values()]

    #Groq
    client = Groq(api_key="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")
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Can you give me a location and activity on the Monash Clayton Campus in Melbourne, Victoria that can satisfy one of these activities for a group of individuals: {', '.join(all_interests)} at the time {event_time}. Make sure that the information you give is ONLY the location and the activity to do and not any more details, just give the location and activity in 2-3 words do not elaborate any further. Also make sure to put the location in quotation marks. Also provide the general location as well that's within the Clayton Campus like the area. Some suggestions are badminton courts, basketball courts, gym, MEGA PC Gaming lounge (you must say its the MEGA PC Gaming lounge) in the Campus centre basement, The Arcade which has 'billiard tables, foosball, dartboards, air hockey, video games' at the sports facility (suggested for people with very mixed interests), and a walk around the Campus's lake.",
            }
        ],
        model="llama-3.3-70b-versatile",
        stream=False,
    )
    suggested_location = chat_completion.choices[0].message.content.strip()

    return {
        "message": "Common interests determined",
        "all_interests": all_interests,
        "suggested_location": suggested_location,
    }
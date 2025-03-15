import logging
import random
import string
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from web.user_auth import get_user

import jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")

import config
from models.user_models import UserDto
from modules.db import CollectionRef, UserRef
from web.auth import require_api_key
from web.user_auth import get_password_hash

from itsdangerous import URLSafeTimedSerializer
from modules.mail import mail, create_message

_log = logging.getLogger("uvicorn")
router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/by-uuid/{user_id}")
async def get_user_by_uuid(user_id: str) -> dict:
    user_collection = await config.db.get_collection(CollectionRef.USERS)
    user = await user_collection.find_one({UserRef.ID: user_id})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    else:
        return user


@router.get("/by-email/{email}")
async def get_user_by_email(email: str) -> dict:
    user_collection = await config.db.get_collection(CollectionRef.USERS)
    user = await user_collection.find_one({UserRef.EMAIL: email})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    else:
        return user

serializer = URLSafeTimedSerializer(
    secret_key=SECRET_KEY, salt="email-verification"
)

def create_url_safe_token(data: dict):


    token = serializer.dumps(data)

    return token

def decode_url_safe_token(token: str):
    try:
        token_data = serializer.loads(token)

        return token_data
    except Exception as e:
        logging.error(str(e))


# NOTE: A follow-up POST users/account/reset-password must be sent.
@router.post("/")
async def register_user(user: UserDto) -> dict:
    user_collection = await config.db.get_collection(CollectionRef.USERS)
    user.id = str(uuid.uuid4())  # UUID4 will always be unique
    # if await user_collection.find_one({UserRef.ID: user.id}):
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="User with the same id already exists",
    #     )


    if await user_collection.find_one({UserRef.EMAIL: user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with the same email already exists",
        )

    random_password = "".join(random.choices(string.ascii_letters, k=32))
    user.hashed_password = get_password_hash(random_password)

        # send the email verification to the user
        #user.email
    token = create_url_safe_token({"email": user.email})
    link = "http://localhost:3000/verify" + token
    html_messsage = f"""
    <h1>Verify your Email</h1>
    <p>Please click the <a href="{link}">link</a> below to verify your email address</p>
    """

    await mail.send_message(
        create_message(
            recipients=[user.email],
            subject="Verify your email",
            body=html_messsage,
        )
    )

    await user_collection.insert_one(user.model_dump())

    _log.info(f"User {user.id} created")

    return {"message": "User created", "user": user}

@router.post("/verify/{token}")
async def verify_user(token:str):
    tokenData = decode_url_safe_token(token)

    user_email = tokenData.get("email")
    
    if user_email:
        user = get_user(user_email)
        if user:
            user_collection = await config.db.get_collection(CollectionRef.USERS)

            user.account_verified = True
            await user_collection.update_one({UserRef.ID: user.id}, {"$set": user.model_dump_safe()})

            return {"message": "User email has been successfully verified"}


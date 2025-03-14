from enum import StrEnum


class UserRef(StrEnum):
    ID = "_id"
    NAME = "name"
    EMAIL = "email"
    HASHED_PASSWORD = "hashed_password"

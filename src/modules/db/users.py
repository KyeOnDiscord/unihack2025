from enum import StrEnum


class UserRef(StrEnum):
    ID = "_id"
    NAME = "name"
    EMAIL = "email"
    PASSWORD_HASH = "password_hash"

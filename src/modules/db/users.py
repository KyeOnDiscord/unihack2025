from enum import StrEnum


class UserRef(StrEnum):
    ID = "_id"
    NAME = "name"
    EMAIL = "email"
    CALENDER_ICS_LINK = "calender_ics_link"
    PREFERENCES = "preferences"
    HASHED_PASSWORD = "hashed_password"
    DISABLED = "disabled"

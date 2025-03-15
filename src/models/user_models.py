# Chuck in anything related to the user model here.
# e.g. The user itself, maybe user settings (if separated) etc.

from .generic import DBRecord
from typing import Optional


class UserDto(DBRecord):
    id: Optional[str] = None
    name: str
    email: str
    calender_ics_link: Optional[str] = None
    preferences: Optional[str] = None
    hashed_password: Optional[str] = None
    disabled: bool = False

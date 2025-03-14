# Chuck in anything related to the user model here.
# e.g. The user itself, maybe user settings (if separated) etc.

from .generic import DBRecord


class UserDto(DBRecord):
    id: int
    name: str
    email: str
    password_hash: str

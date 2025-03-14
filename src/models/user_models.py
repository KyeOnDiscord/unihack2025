# Chuck in anything related to the user model here.
# e.g. The user itself, maybe user settings (if separated) etc.

from pydantic import BaseModel


class UserDto(BaseModel):
    id: int
    name: str
    email: str
    password_hash: str

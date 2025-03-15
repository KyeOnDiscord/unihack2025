# Chuck in anything related to the room model here.
# e.g. The rooms, users they hold, and id

from .generic import DBRecord
from typing import Optional, List


class RoomDto(DBRecord):
    id: Optional[str] = None
    name: str
    room_code: Optional[str] = None
    owner_id: Optional[str] = None
    users: List[str] = []

# Chuck in anything related to the room model here.
# e.g. The rooms, users they hold, and id

from .generic import DBRecord
from typing import Optional, List

class RoomDto(DBRecord):
    id: Optional[str] = None
    name: str
    owner_id: str
    users: List[str] = []

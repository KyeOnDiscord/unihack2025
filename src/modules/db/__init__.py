import os
import logging

from astrapy import DataAPIClient, AsyncDatabase

from .collections import CollectionRef
from .users import UserRef
from .rooms import RoomRef

__all__ = ["get_db", "UserRef", "CollectionRef", "RoomRef"]

_log = logging.getLogger("uvicorn")


def get_db(endpoint: str, token: str = None) -> AsyncDatabase:
    token = token if token is not None else os.getenv("ASTRA_DB_APPLICATION_TOKEN")

    client = DataAPIClient(token)

    db = client.get_async_database(endpoint)

    _log.info(f"Connected to database {db.info().name}")

    return db

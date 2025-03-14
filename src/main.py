from __future__ import annotations

import importlib
import logging
import os
import yaml

from dotenv import load_dotenv
from fastapi import FastAPI
from typing import TYPE_CHECKING

import config

if TYPE_CHECKING:
    from fastapi import APIRouter

# FastAPI requires a global variable named 'app' to be defined as the FastAPI
# instance.
app = FastAPI()
config.app = app
_log = logging.getLogger("uvicorn")
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_CONFIG_DIR = os.path.join(BASE_DIR, "configs", "app_config.yaml")
ROUTERS_DIR = os.path.join(BASE_DIR, "web", "routers")


def _get_config() -> None:
    if not os.path.exists(APP_CONFIG_DIR):
        raise FileNotFoundError(f"App config file not found. Should be at {APP_CONFIG_DIR}")

    with open(APP_CONFIG_DIR, "r") as f:
        config.app_config = yaml.safe_load(f)

def _import_routers() -> None:
    for filename in os.listdir(ROUTERS_DIR):
        if not filename.endswith(".py"):
            continue

        relative_dir = ROUTERS_DIR.replace(BASE_DIR, "")[1:]
        module = importlib.import_module(f"{relative_dir.replace('\\', '.')}.{filename[:-3]}")
        if hasattr(module, "router"):
            router: APIRouter = getattr(module, "router")
            app.include_router(router)
            _log.info(f"Included router: {filename[:-3]}")


# Don't use if __name__ == "__main__": here.
# Can't use `fastapi` command otherwise.
_get_config()
_import_routers()

_log.info("App initialized")

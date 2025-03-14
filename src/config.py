# See https://docs.python.org/3/faq/programming.html#how-do-i-share-global-variables-across-modules

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

    from models.config_models import AppConfigDto


app: FastAPI = None
app_config: AppConfigDto = None

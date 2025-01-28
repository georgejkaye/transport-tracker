import uvicorn

from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException

from api.data.stats import Stats, get_train_stats
from api.utils.database import connect
from api.utils.environment import get_env_variable
from api.data.leg import ShortLeg, select_legs
from api.data.stations import (
    StationData,
    select_station,
    select_stations,
)

from api.api.routers.train import train


app = FastAPI(
    title="Train tracker API",
    summary="API for interacting with the train tracker",
    version="1.0.0",
    contact={
        "name": "George Kaye",
        "email": "georgejkaye@gmail.com",
        "url": "https://georgejkaye.com",
    },
    license_info={
        "name": "GNU General Public License v3.0",
        "url": "https://www.gnu.org/licenses/gpl-3.0.en.html",
    },
)

app.include_router(train.router)


def start():
    if get_env_variable("API_ENV") == "prod":
        reload = False
    elif get_env_variable("API_ENV") == "dev":
        reload = True
    else:
        raise RuntimeError("API_ENV not set")
    port_var = get_env_variable("API_PORT")
    if port_var is None:
        port = 8000
    elif not port_var.isnumeric():
        raise RuntimeError(f"API_PORT must be number but it is {port_var}")
    else:
        port = int(port_var)
    uvicorn.run(
        "api.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    start()

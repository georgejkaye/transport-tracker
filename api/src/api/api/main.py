from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException

from api.data.database import connect, disconnect
from api.data.environment import get_env_variable
from api.data.leg import ShortLeg, select_legs

import uvicorn

from api.data.stations import ShortTrainStation, select_station_from_crs

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


@app.get("/legs", summary="Get legs")
async def get_legs(
    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
) -> list[ShortLeg]:
    (conn, cur) = connect()
    legs = select_legs(cur, start_date, end_date)
    disconnect(conn, cur)
    return legs


@app.get("/train/leg/{leg_id}", summary="Get train leg")
async def get_leg(leg_id: int) -> ShortLeg:
    (conn, cur) = connect()
    legs = select_legs(cur, search_leg_id=leg_id)
    disconnect(conn, cur)
    if len(legs) != 1:
        raise HTTPException(status_code=404, detail="Leg not found")
    return legs[0]


@app.get("/train/station/{station_crs}", summary="Get train station")
async def get_train_station(station_crs: str) -> ShortTrainStation:
    (conn, cur) = connect()
    station = select_station_from_crs(cur, station_crs)
    disconnect(conn, cur)
    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")
    return ShortTrainStation(station.name, station.crs)


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

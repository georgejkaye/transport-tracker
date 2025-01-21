import uvicorn

from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from api.data.stats import Stats, get_stats
from api.data.database import connect
from api.data.environment import get_env_variable
from api.data.leg import ShortLeg, select_legs
from api.data.stations import (
    StationData,
    get_station_points_from_crses,
    select_station,
    select_station_from_crs,
    select_stations,
)
from api.data.map import (
    LegLine,
    make_leg_map,
)
from api.data.network import find_shortest_path_between_stations

from api.api.network import network
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


@app.get("/train", summary="Get train stats across an optional range")
async def get_train_stats(
    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
) -> Stats:
    with connect() as (conn, _):
        try:
            return get_stats(conn, start_date, end_date)
        except RuntimeError:
            raise HTTPException(500, "Could not get stats")


@app.get("/train/year/{year}", summary="Get train stats across a year")
async def get_train_stats_from_year(
    year: int,
) -> Stats:
    with connect() as (conn, _):
        try:
            return get_stats(conn, datetime(year, 1, 1), datetime(year, 12, 31))
        except RuntimeError:
            raise HTTPException(500, "Could not get stats")


@app.get(
    "/train/route",
    summary="Get route between two stations",
    response_class=HTMLResponse,
)
async def get_route_between_stations(
    from_crs: str,
    to_crs: str,
    from_platform: Optional[str] = None,
    to_platform: Optional[str] = None,
) -> str:
    with connect() as (conn, cur):
        from_station = select_station_from_crs(cur, from_crs)
        if from_station is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not find station for code {from_crs}",
            )
        to_station = select_station_from_crs(cur, to_crs)
        if to_station is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not find station for code {to_crs}",
            )
        station_points = get_station_points_from_crses(
            conn, [(from_crs, from_platform), (to_crs, to_platform)]
        )
        (_, path) = find_shortest_path_between_stations(
            network,
            conn,
            from_crs,
            from_platform,
            to_crs,
            to_platform,
            station_points,
        )
        if path is None:
            raise HTTPException(
                status_code=404,
                detail="Could not find a route between these stations",
            )
        return make_leg_map(
            [],
            [
                LegLine(
                    from_station.name, to_station.name, path, "#000000", 0, 0
                )
            ],
        )


@app.get("/train/legs", summary="Get legs")
async def get_legs(
    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
) -> list[ShortLeg]:
    with connect() as (conn, _):
        legs = select_legs(conn, start_date, end_date)
        return legs


@app.get("/train/legs/year/{year}", summary="Get legs")
async def get_legs_from_year(year: int) -> list[ShortLeg]:
    with connect() as (conn, _):
        legs = select_legs(conn, datetime(year, 1, 1), datetime(year, 12, 31))
        return legs


@app.get("/train/leg/{leg_id}", summary="Get train leg")
async def get_leg(leg_id: int) -> ShortLeg:
    with connect() as (conn, _):
        legs = select_legs(conn, search_leg_id=leg_id)
        if len(legs) != 1:
            raise HTTPException(status_code=404, detail="Leg not found")
        return legs[0]


@app.get("/train/stations", summary="Get train stations")
async def get_train_stations() -> list[StationData]:
    with connect() as (_, cur):
        stations = select_stations(cur)
        return stations


@app.get("/train/station/{station_crs}", summary="Get train station")
async def get_train_station(station_crs: str) -> StationData:
    with connect() as (_, cur):
        station = select_station(cur, station_crs)
        if station is None:
            raise HTTPException(status_code=404, detail="Station not found")
        return station


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

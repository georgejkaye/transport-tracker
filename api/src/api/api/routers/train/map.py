from datetime import datetime
from typing import Optional
from api.data.leg import select_legs
from api.data.stations import (
    get_station_points_from_crses,
    select_station_from_crs,
)
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from api.data import network
from api.data.database import connect
from api.data.map import (
    LegLine,
    StationPair,
    get_leg_map_page,
    get_leg_map_page_from_station_pair_list,
    make_leg_map,
)
from api.data.network import find_shortest_path_between_stations
from api.api.network import network
from urllib3 import HTTPResponse

router = APIRouter(prefix="/map")


@router.get(
    "/",
    summary="Get map of train journeys across a time period",
    response_class=HTMLResponse,
)
async def get_train_map_from_time_period(
    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
) -> str:
    with connect() as (conn, _):
        try:
            return get_leg_map_page(network, conn, start_date, end_date)
        except RuntimeError:
            raise HTTPException(500, "Could not get stats")


@router.get(
    "/year/{year}",
    summary="Get map of train journeys across a year",
    response_class=HTMLResponse,
)
async def get_train_map_from_year(year: int) -> str:
    with connect() as (conn, _):
        try:
            return get_leg_map_page(
                network, conn, datetime(year, 1, 1), datetime(year, 12, 31)
            )
        except RuntimeError:
            raise HTTPException(500, "Could not get stats")


@router.post(
    "/data",
    summary="Get map of train journeys from a data set",
    response_class=HTMLResponse,
)
async def get_train_map_from_data(data: list[StationPair]) -> str:
    with connect() as (conn, _):
        try:
            return get_leg_map_page_from_station_pair_list(network, conn, data)
        except RuntimeError:
            raise HTTPException(500, "Could not get all stations")
        except KeyError as e:
            raise HTTPException(
                422,
                f"Could not find station {str(e)}; please use the station name as it appears on RealTime Trains",
            )


@router.get(
    "/route",
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
        path = find_shortest_path_between_stations(
            network,
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
                    from_station.name,
                    to_station.name,
                    path,
                    "#000000",
                    0,
                    0,
                )
            ],
        )


@router.get(
    "/leg/{leg_id}", summary="Get a map for a leg", response_class=HTMLResponse
)
async def get_leg_map(leg_id: int) -> str:
    with connect() as (conn, _):
        return get_leg_map_page(network, conn, search_leg_id=leg_id)

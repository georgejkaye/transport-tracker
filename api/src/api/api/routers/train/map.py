from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from api.data import network
from api.data.database import connect
from api.data.map import (
    StationPair,
    get_leg_map_page,
    get_leg_map_page_from_station_pair_list,
)
from api.api.network import network

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

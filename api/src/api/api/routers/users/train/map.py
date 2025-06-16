from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from api.utils.database import connect_with_env
from api.classes.network.map import CallInfo, StationInfo
from api.network.map import get_leg_map_page
from api.api.network import network

router = APIRouter(prefix="/map", tags=["users/train/map"])


@router.get(
    "",
    summary="Get map of train legs across a time period",
    response_class=HTMLResponse,
)
async def get_train_map_from_time_period(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> str:
    with connect_with_env() as conn:
        try:
            return get_leg_map_page(
                network, conn, user_id, StationInfo(True), start_date, end_date
            )
        except RuntimeError:
            raise HTTPException(500, "Could not get stats")


@router.get(
    "/year/{year}",
    summary="Get map of train legs across a year",
    response_class=HTMLResponse,
)
async def get_train_map_from_year(user_id: int, year: int) -> str:
    with connect_with_env() as conn:
        try:
            return get_leg_map_page(
                network,
                conn,
                user_id,
                StationInfo(True),
                datetime(year, 1, 1),
                datetime(year, 12, 31),
            )
        except RuntimeError:
            raise HTTPException(500, "Could not get stats")


@router.get(
    "/legs/{leg_id}",
    summary="Get a map for a particular train leg",
    response_class=HTMLResponse,
)
async def get_leg_map_for_leg_id(user_id: int, leg_id: int) -> str:
    with connect_with_env() as conn:
        return get_leg_map_page(
            network, conn, user_id, CallInfo(), search_leg_id=leg_id
        )

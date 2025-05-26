from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Optional

from api.utils.database import connect_with_env
from api.data.bus.leg import (
    BusLegUserDetails,
    select_bus_leg_by_id,
    select_bus_legs,
    select_bus_legs_by_datetime,
    select_bus_legs_by_end_datetime,
    select_bus_legs_by_start_datetime,
)


router = APIRouter(prefix="/legs", tags=["users/bus/legs"])


@router.get("", summary="Get details of all bus legs for a user")
async def get_legs(
    user_id: int,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
) -> list[BusLegUserDetails]:
    with connect_with_env() as conn:
        if search_start and search_end:
            legs = select_bus_legs_by_datetime(
                conn, user_id, search_start, search_end
            )
        elif search_start:
            legs = select_bus_legs_by_start_datetime(
                conn, user_id, search_start
            )
        elif search_end:
            legs = select_bus_legs_by_end_datetime(conn, user_id, search_end)
        else:
            legs = select_bus_legs(conn, user_id)
        return legs


@router.get("/{leg_id}", summary="Get details of a bus leg for a user")
async def get_leg_by_id(user_id, leg_id: int) -> BusLegUserDetails:
    with connect_with_env() as conn:
        leg = select_bus_leg_by_id(conn, user_id, leg_id)
        if leg is None:
            raise HTTPException(404, "Could not find leg or user")
        return leg


@router.get(
    "/years/{year}", summary="Get details of all bus legs for a user in a year"
)
async def get_legs_by_year(user_id, year: int) -> list[BusLegUserDetails]:
    with connect_with_env() as conn:
        legs = select_bus_legs_by_datetime(
            conn, user_id, datetime(year, 1, 1), datetime(year, 12, 31)
        )
        return legs

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from api.api.lifespan import get_db_connection
from api.classes.bus.leg import BusLegUserDetails
from api.db.bus.leg import (
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
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[BusLegUserDetails]:
    conn = get_db_connection()
    if start_date and end_date:
        legs = select_bus_legs_by_datetime(conn, user_id, start_date, end_date)
    elif start_date:
        legs = select_bus_legs_by_start_datetime(conn, user_id, start_date)
    elif end_date:
        legs = select_bus_legs_by_end_datetime(conn, user_id, end_date)
    else:
        legs = select_bus_legs(conn, user_id)
    return legs


@router.get("/{leg_id}", summary="Get details of a bus leg for a user")
async def get_leg_by_id(user_id: int, leg_id: int) -> BusLegUserDetails:
    leg = select_bus_leg_by_id(get_db_connection(), user_id, leg_id)
    if leg is None:
        raise HTTPException(404, "Could not find leg or user")
    return leg


@router.get(
    "/years/{year}", summary="Get details of all bus legs for a user in a year"
)
async def get_legs_by_year(user_id: int, year: int) -> list[BusLegUserDetails]:
    legs = select_bus_legs_by_datetime(
        get_db_connection(),
        user_id,
        datetime(year, 1, 1),
        datetime(year, 12, 31),
    )
    return legs

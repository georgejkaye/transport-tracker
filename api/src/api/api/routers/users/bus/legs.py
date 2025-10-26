from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from api.api.lifespan import get_db_connection
from api.db.functions.select.bus import (
    select_bus_leg_user_details_by_user_id_and_datetime_fetchall,
    select_bus_leg_user_details_by_user_id_and_end_datetime_fetchall,
    select_bus_leg_user_details_by_user_id_and_leg_id_fetchone,
    select_bus_leg_user_details_by_user_id_and_start_datetime_fetchall,
    select_bus_leg_user_details_fetchall,
)
from api.db.types.bus import BusLegUserDetails

router = APIRouter(prefix="/legs", tags=["users/bus/legs"])


@router.get("", summary="Get details of all bus legs for a user")
async def get_legs(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[BusLegUserDetails]:
    conn = get_db_connection()
    if start_date and end_date:
        legs = select_bus_leg_user_details_by_user_id_and_datetime_fetchall(
            conn, user_id, start_date, end_date
        )
    elif start_date:
        legs = (
            select_bus_leg_user_details_by_user_id_and_start_datetime_fetchall(
                conn, user_id, start_date
            )
        )
    elif end_date:
        legs = select_bus_leg_user_details_by_user_id_and_end_datetime_fetchall(
            conn, user_id, end_date
        )
    else:
        legs = select_bus_leg_user_details_fetchall(conn, user_id)
    return legs


@router.get("/{leg_id}", summary="Get details of a bus leg for a user")
async def get_leg_by_id(user_id: int, leg_id: int) -> BusLegUserDetails:
    leg = select_bus_leg_user_details_by_user_id_and_leg_id_fetchone(
        get_db_connection(), user_id, leg_id
    )
    if leg is None:
        raise HTTPException(404, "Could not find leg or user")
    return leg


@router.get(
    "/years/{year}", summary="Get details of all bus legs for a user in a year"
)
async def get_legs_by_year(user_id: int, year: int) -> list[BusLegUserDetails]:
    legs = select_bus_leg_user_details_by_user_id_and_datetime_fetchall(
        get_db_connection(),
        user_id,
        datetime(year, 1, 1),
        datetime(year, 12, 31),
    )
    return legs

from fastapi import APIRouter
from datetime import datetime
from typing import Optional

from api.utils.database import connect_with_env
from api.data.bus.leg import (
    BusLeg,
    select_bus_leg_by_id,
    select_bus_legs,
    select_bus_legs_by_datetime,
    select_bus_legs_by_end_datetime,
    select_bus_legs_by_start_datetime,
)


router = APIRouter(prefix="/legs", tags=["users/bus/legs"])


@router.get("", summary="Get bus legs")
async def get_legs(
    user_id: int,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
) -> list[BusLeg]:
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


@router.get("/{id}", summary="Get bus leg with id")
async def get_leg_by_id(user_id, leg_id: int) -> BusLeg:
    with connect_with_env() as conn:
        leg = select_bus_leg_by_id(conn, user_id, leg_id)
        return leg

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


router = APIRouter(prefix="/legs", tags=["bus/legs"])


@router.get("", summary="Get bus legs")
async def get_legs(
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
) -> list[BusLeg]:
    with connect_with_env() as conn:
        if search_start and search_end:
            legs = select_bus_legs_by_datetime(conn, search_start, search_end)
        elif search_start:
            legs = select_bus_legs_by_start_datetime(conn, search_start)
        elif search_end:
            legs = select_bus_legs_by_end_datetime(conn, search_end)
        else:
            legs = select_bus_legs(conn)
        return legs


@router.get("/{id}", summary="Get bus leg with id")
async def get_leg_by_id(id: int) -> BusLeg:
    with connect_with_env() as conn:
        leg = select_bus_leg_by_id(conn, id)
        return leg

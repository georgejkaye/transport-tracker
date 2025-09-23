from fastapi import APIRouter, HTTPException

from api.api.lifespan import get_db_connection
from api.db.bus.user.stop import (
    BusStopUserDetails,
    get_user_details_for_bus_stop,
    get_user_details_for_bus_stop_by_atco,
    get_user_details_for_bus_stops,
)

router = APIRouter(prefix="/stops", tags=["users/bus/stops"])


@router.get("/", summary="Get details of all bus stops for a user")
async def get_bus_stops(user_id: int) -> list[BusStopUserDetails]:
    stops = get_user_details_for_bus_stops(get_db_connection(), user_id)
    return stops


@router.get("/{stop_id}", summary="Get details of a bus stop for a user")
async def get_bus_stop(user_id: int, stop_id: int) -> BusStopUserDetails:
    stop = get_user_details_for_bus_stop(get_db_connection(), user_id, stop_id)
    if stop is None:
        raise HTTPException(404, "Could not find user or stop")
    return stop


@router.get("/atco/{atco}", summary="Get details of a bus stop for a user")
async def get_bus_stop_by_atco(user_id: int, atco: str) -> BusStopUserDetails:
    stop = get_user_details_for_bus_stop_by_atco(
        get_db_connection(), user_id, atco
    )
    if stop is None:
        raise HTTPException(404, "Could not find user or stop")
    return stop

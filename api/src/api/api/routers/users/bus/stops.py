from api.db.bus.user.stop import (
    BusStopUserDetails,
    get_user_details_for_bus_stop,
    get_user_details_for_bus_stop_by_atco,
    get_user_details_for_bus_stops,
)
from api.utils.database import connect_with_env
from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/stops", tags=["users/bus/stops"])


@router.get("/", summary="Get details of all bus stop for a user")
async def get_bus_stops(user_id: int) -> list[BusStopUserDetails]:
    with connect_with_env() as conn:
        stop = get_user_details_for_bus_stops(conn, user_id)
        if stop is None:
            raise HTTPException(404, "Could not find user")
        return stop


@router.get("/{stop_id}", summary="Get details of a bus stop for a user")
async def get_bus_stop(user_id: int, stop_id: int) -> BusStopUserDetails:
    with connect_with_env() as conn:
        stop = get_user_details_for_bus_stop(conn, user_id, stop_id)
        if stop is None:
            raise HTTPException(404, "Could not find user or stop")
        return stop


@router.get("/atco/{atco}", summary="Get details of a bus stop for a user")
async def get_bus_stop_by_atco(user_id: int, atco: str) -> BusStopUserDetails:
    with connect_with_env() as conn:
        stop = get_user_details_for_bus_stop_by_atco(conn, user_id, atco)
        if stop is None:
            raise HTTPException(404, "Could not find user or stop")
        return stop

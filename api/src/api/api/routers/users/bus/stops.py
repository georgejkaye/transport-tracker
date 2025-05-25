from api.data.bus.user.stop import BusStopUserDetails, get_bus_stop_user_details
from api.utils.database import connect_with_env
from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/stops", tags=["users/bus/stops"])


@router.get("/{stop_id}", summary="Get details of a bus stop for a user")
async def get_bus_stop(user_id: int, stop_id: int) -> BusStopUserDetails:
    with connect_with_env() as conn:
        stop = get_bus_stop_user_details(conn, user_id, stop_id)
        if stop is None:
            raise HTTPException(404, "Could not find stop")
        return stop

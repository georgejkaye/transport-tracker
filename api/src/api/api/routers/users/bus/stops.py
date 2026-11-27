from api.db.functions.select.bus.user.stop import (
    select_transport_user_bus_stop_details_by_user_id_and_atco_fetchone,
    select_transport_user_bus_stop_details_by_user_id_and_stop_id_fetchone,
    select_transport_user_bus_stop_summaries_by_user_id_fetchall,
)
from api.db.types.bus.user.stop import (
    TransportUserBusStopDetails,
    TransportUserBusStopSummary,
)
from fastapi import APIRouter, HTTPException

from api.api.lifespan import get_db_connection

router = APIRouter(prefix="/stops", tags=["users/bus/stops"])


@router.get("/", summary="Get details of all bus stops for a user")
async def get_bus_stops(user_id: int) -> list[TransportUserBusStopSummary]:
    stops = select_transport_user_bus_stop_summaries_by_user_id_fetchall(
        get_db_connection(), user_id
    )
    return stops


@router.get("/{stop_id}", summary="Get details of a bus stop for a user")
async def get_bus_stop(
    user_id: int, stop_id: int
) -> TransportUserBusStopDetails:
    stop = (
        select_transport_user_bus_stop_details_by_user_id_and_stop_id_fetchone(
            get_db_connection(), user_id, stop_id
        )
    )
    if stop is None:
        raise HTTPException(404, "Could not find user or stop")
    return stop


@router.get("/atco/{atco}", summary="Get details of a bus stop for a user")
async def get_bus_stop_by_atco(
    user_id: int, atco: str
) -> TransportUserBusStopDetails:
    stop = select_transport_user_bus_stop_details_by_user_id_and_atco_fetchone(
        get_db_connection(), user_id, atco
    )
    if stop is None:
        raise HTTPException(404, "Could not find user or stop")
    return stop

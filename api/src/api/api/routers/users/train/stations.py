from fastapi import APIRouter, HTTPException

from api.api.lifespan import get_db_connection
from api.db.functions.select.train.user import (
    select_transport_user_train_station_by_user_id_fetchone,
    select_transport_user_train_stations_by_user_id_fetchall,
)
from api.db.types.user.train.station import TransportUserTrainStationOutData

router = APIRouter(prefix="/stations", tags=["users/train/stations"])


@router.get("", summary="Get train station data for a user")
async def get_train_stations(
    user_id: int,
) -> list[TransportUserTrainStationOutData]:
    stations = select_transport_user_train_stations_by_user_id_fetchall(
        get_db_connection(), user_id
    )
    return stations


@router.get(
    "/{train_station_id}",
    summary="Get train station data for a user and a particular station",
)
async def get_train_station(
    user_id: int, train_station_id: int
) -> TransportUserTrainStationOutData:
    station = select_transport_user_train_station_by_user_id_fetchone(
        get_db_connection(), user_id, train_station_id
    )
    if station is None:
        raise HTTPException(
            status_code=404,
            detail=f"Train station id {train_station_id} not found",
        )
    return station


# @router.get("/{station_crs}", summary="Get train station")
# async def get_train_station(user_id: int, station_crs: str) -> StationData:
#     station = select_station(get_db_connection(), station_crs)
#     if station is None:
#         raise HTTPException(status_code=404, detail="Station not found")
#     return station

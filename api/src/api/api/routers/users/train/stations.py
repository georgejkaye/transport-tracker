from datetime import datetime

from fastapi import APIRouter, HTTPException

from api.api.lifespan import get_db_connection
from api.db.functions.select.train.user.station import (
    select_transport_user_train_station_by_user_id_and_station_crs_fetchone,
    select_transport_user_train_station_by_user_id_and_station_id_fetchone,
    select_transport_user_train_stations_by_user_id_fetchall,
)
from api.db.types.user.train.station import (
    TransportUserTrainStationHighOutData,
    TransportUserTrainStationOutData,
)

router = APIRouter(prefix="/stations", tags=["users/train/stations"])


@router.get("", summary="Get train station data for a user")
async def get_train_stations(
    user_id: int, search_start: datetime, search_end: datetime
) -> list[TransportUserTrainStationHighOutData]:
    stations = select_transport_user_train_stations_by_user_id_fetchall(
        get_db_connection(), user_id, search_start, search_end
    )
    return stations


@router.get(
    "/years/{year}", summary="Get train station data for a user in a given year"
)
async def get_train_stations_by_year(
    user_id: int, year: int
) -> list[TransportUserTrainStationHighOutData]:
    stations = select_transport_user_train_stations_by_user_id_fetchall(
        get_db_connection(),
        user_id,
        datetime(year, 1, 1),
        datetime(year + 1, 1, 1),
    )
    return stations


@router.get(
    "/{station_id}",
    summary="Get train station data for a user and a particular station",
)
async def get_train_station(
    user_id: int, station_id: int, search_start: datetime, search_end: datetime
) -> TransportUserTrainStationOutData:
    station = (
        select_transport_user_train_station_by_user_id_and_station_id_fetchone(
            get_db_connection(), user_id, station_id, search_start, search_end
        )
    )
    if station is None:
        raise HTTPException(
            status_code=404,
            detail=f"Train station id {station_id} not found",
        )
    return station


@router.get(
    "/{station_id}/years/{year}",
    summary="Get train station data for a user and a particular station",
)
async def get_train_station_by_year(
    user_id: int, station_id: int, year: int
) -> TransportUserTrainStationOutData:
    station = (
        select_transport_user_train_station_by_user_id_and_station_id_fetchone(
            get_db_connection(),
            user_id,
            station_id,
            datetime(year, 1, 1),
            datetime(year + 1, 1, 1),
        )
    )
    if station is None:
        raise HTTPException(
            status_code=404,
            detail=f"Train station id {station_id} not found",
        )
    return station


@router.get("/crs/{station_crs}", summary="Get train station")
async def get_train_station_by_crs(
    user_id: int, station_crs: str, search_start: datetime, search_end: datetime
) -> TransportUserTrainStationOutData:
    station = (
        select_transport_user_train_station_by_user_id_and_station_crs_fetchone(
            get_db_connection(), user_id, station_crs, search_start, search_end
        )
    )
    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")
    return station


@router.get(
    "/crs/{station_crs}/years/{year}",
    summary="Get train station data for a user in a given year",
)
async def get_train_station_by_crs_and_year(
    user_id: int, station_crs: str, year: int
) -> TransportUserTrainStationOutData:
    station = (
        select_transport_user_train_station_by_user_id_and_station_crs_fetchone(
            get_db_connection(),
            user_id,
            station_crs,
            datetime(year, 1, 1),
            datetime(year + 1, 1, 1),
        )
    )
    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")
    return station

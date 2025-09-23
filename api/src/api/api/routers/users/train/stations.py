from fastapi import APIRouter, HTTPException

from api.api.lifespan import get_db_connection
from api.classes.train.station import StationData
from api.db.train.stations import (
    select_station,
    select_stations,
)

router = APIRouter(prefix="/stations", tags=["users/train/stations"])


@router.get("", summary="Get train stations")
async def get_train_stations(user_id: int) -> list[StationData]:
    stations = select_stations(get_db_connection())
    return stations


@router.get("/{station_crs}", summary="Get train station")
async def get_train_station(user_id: int, station_crs: str) -> StationData:
    station = select_station(get_db_connection(), station_crs)
    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")
    return station

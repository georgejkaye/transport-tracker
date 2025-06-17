from fastapi import APIRouter, HTTPException

from api.classes.train.station import StationData
from api.db.train.stations import (
    select_station,
    select_stations,
)
from api.utils.database import connect_with_env

router = APIRouter(prefix="/stations", tags=["users/train/stations"])


@router.get("", summary="Get train stations")
async def get_train_stations(user_id: int) -> list[StationData]:
    with connect_with_env() as conn:
        stations = select_stations(conn)
        return stations


@router.get("/{station_crs}", summary="Get train station")
async def get_train_station(user_id: int, station_crs: str) -> StationData:
    with connect_with_env() as conn:
        station = select_station(conn, station_crs)
        if station is None:
            raise HTTPException(status_code=404, detail="Station not found")
        return station

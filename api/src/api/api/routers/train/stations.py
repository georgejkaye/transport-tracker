from api.data.stations import StationData, select_station, select_stations
from api.utils.database import connect_with_env
from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/stations", tags=["train/stations"])


@router.get("", summary="Get train stations")
async def get_train_stations() -> list[StationData]:
    with connect_with_env() as conn:
        stations = select_stations(conn)
        return stations


@router.get("/{station_crs}", summary="Get train station")
async def get_train_station(station_crs: str) -> StationData:
    with connect_with_env() as conn:
        station = select_station(conn, station_crs)
        if station is None:
            raise HTTPException(status_code=404, detail="Station not found")
        return station

from api.data.bus.overview import (
    BusVehicleOverview,
    get_bus_vehicle_overviews_for_user,
)
from api.utils.database import connect_with_env
from fastapi import APIRouter


router = APIRouter(prefix="/vehicles", tags=["bus/vehicles"])


@router.get("/{user}", summary="Get bus vehicles for a user")
async def get_vehicles_for_user(user: int) -> list[BusVehicleOverview]:
    with connect_with_env() as conn:
        vehicles = get_bus_vehicle_overviews_for_user(conn, user)
        return vehicles

from api.data.bus.overview import (
    BusVehicleUserDetails,
    get_bus_vehicle_overviews_for_user,
)
from api.utils.database import connect_with_env
from fastapi import APIRouter


router = APIRouter(prefix="/vehicles", tags=["users/bus/vehicles"])


@router.get("/", summary="Get bus vehicles for a user")
async def get_vehicles_for_user(user_id: int) -> list[BusVehicleUserDetails]:
    with connect_with_env() as conn:
        vehicles = get_bus_vehicle_overviews_for_user(conn, user_id)
        return vehicles

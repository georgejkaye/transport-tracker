from api.data.bus.overview import (
    BusVehicleUserDetails,
    get_bus_vehicle_overview_for_user,
    get_bus_vehicle_overviews_for_user,
)
from api.utils.database import connect_with_env
from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/vehicles", tags=["users/bus/vehicles"])


@router.get("/", summary="Get bus vehicles for a user")
async def get_vehicles_for_user(user_id: int) -> list[BusVehicleUserDetails]:
    with connect_with_env() as conn:
        vehicles = get_bus_vehicle_overviews_for_user(conn, user_id)
        return vehicles


@router.get("/{vehicle_id}", summary="Get bus vehicle for a user")
async def get_vehicle_for_user(
    user_id: int, vehicle_id: int
) -> BusVehicleUserDetails:
    with connect_with_env() as conn:
        vehicle = get_bus_vehicle_overview_for_user(conn, user_id, vehicle_id)
        if vehicle is None:
            raise HTTPException(404, "Could not find user or vehicle")
        return vehicle

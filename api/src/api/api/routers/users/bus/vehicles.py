from fastapi import APIRouter, HTTPException

from api.api.lifespan import get_db_connection
from api.db.functions.select.bus import (
    select_bus_vehicle_user_details_by_user_id_and_vehicle_id_fetchone,
    select_bus_vehicle_user_details_by_user_id_fetchall,
)
from api.db.types.bus import BusVehicleUserDetails

router = APIRouter(prefix="/vehicles", tags=["users/bus/vehicles"])


@router.get("/", summary="Get bus vehicles for a user")
async def get_vehicles_for_user(user_id: int) -> list[BusVehicleUserDetails]:
    vehicles = select_bus_vehicle_user_details_by_user_id_fetchall(
        get_db_connection(), user_id
    )
    return vehicles


@router.get("/{vehicle_id}", summary="Get bus vehicle for a user")
async def get_vehicle_for_user(
    user_id: int, vehicle_id: int
) -> BusVehicleUserDetails:
    vehicle = (
        select_bus_vehicle_user_details_by_user_id_and_vehicle_id_fetchone(
            get_db_connection(), user_id, vehicle_id
        )
    )
    if vehicle is None:
        raise HTTPException(404, "Could not find user or vehicle")
    return vehicle

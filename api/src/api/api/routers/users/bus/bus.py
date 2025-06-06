from api.api.routers.users.bus import legs, stops, vehicles
from fastapi import APIRouter

router = APIRouter(prefix="/bus")


router.include_router(legs.router)
router.include_router(stops.router)
router.include_router(vehicles.router)

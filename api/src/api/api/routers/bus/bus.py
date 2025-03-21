from api.api.routers.bus import legs, vehicles
from fastapi import APIRouter

router = APIRouter(prefix="/bus")


router.include_router(legs.router)
router.include_router(vehicles.router)

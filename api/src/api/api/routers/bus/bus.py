from api.api.routers.bus import legs
from fastapi import APIRouter

router = APIRouter(prefix="/bus")


router.include_router(legs.router)

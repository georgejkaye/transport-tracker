from fastapi import APIRouter

from api.api.routers.users.bus import bus
from api.api.routers.users.train import train

router = APIRouter(prefix="/users/{user_id}")

router.include_router(train.router)
router.include_router(bus.router)

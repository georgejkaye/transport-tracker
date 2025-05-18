from fastapi import APIRouter

from api.api.routers.utils import train

router = APIRouter(
    prefix="/utils",
)

router.include_router(train.router)

from fastapi import APIRouter
from api.api.routers.train import map


router = APIRouter(prefix="/train", tags=["train"])

router.include_router(map.router)

from fastapi import APIRouter

from api.api.routers.train import legs

router = APIRouter(prefix="/train")


router.include_router(legs.router)

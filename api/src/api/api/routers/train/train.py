from fastapi import APIRouter
from . import map


router = APIRouter(prefix="/train", tags=["train"])

router.include_router(map.router)

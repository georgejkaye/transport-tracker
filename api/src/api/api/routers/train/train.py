from fastapi import APIRouter

from api.api.routers.train import legs, operators

router = APIRouter(prefix="/train")


router.include_router(legs.router)
router.include_router(operators.router)

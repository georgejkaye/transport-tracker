from fastapi import APIRouter

from api.api.routers.users.train import (
    brands,
    legs,
    maps,
    operators,
    stations,
    stats,
    vehicles,
)

router = APIRouter(prefix="/train")


router.include_router(stats.router)
router.include_router(legs.router)
router.include_router(maps.router)
router.include_router(stations.router)
router.include_router(vehicles.router)
router.include_router(operators.router)
router.include_router(brands.router)

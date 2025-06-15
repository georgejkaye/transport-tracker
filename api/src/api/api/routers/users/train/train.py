from fastapi import APIRouter

from api.api.routers.users.train import legs, map, stations, stats


router = APIRouter(prefix="/train")


router.include_router(stats.router)
router.include_router(stations.router)
router.include_router(legs.router)
router.include_router(map.router)

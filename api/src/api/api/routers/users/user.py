from fastapi import APIRouter, HTTPException

from api.api.lifespan import get_db_connection
from api.api.routers.users.bus import bus
from api.api.routers.users.train import train
from api.stats.classes.user import UserDetails
from api.stats.train import get_user_details

router = APIRouter(prefix="/users/{user_id}")

router.include_router(train.router)
router.include_router(bus.router)


@router.get("", summary="Get transport overview for a user")
async def get_user(user_id: int) -> UserDetails:
    details = get_user_details(get_db_connection(), user_id)
    if details is None:
        raise HTTPException(404, f"Could not get user {user_id}")
    return details

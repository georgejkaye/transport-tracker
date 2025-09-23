from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from api.api.lifespan import (
    get_db_connection,
    get_network,
    get_train_operator_brand_colour,
)
from api.network.map import get_leg_map_page_by_user_id

router = APIRouter(prefix="/legs/maps", tags=["users/train/legs/maps"])


@router.get(
    "",
    summary="Get user train leg map for a time period",
    response_class=HTMLResponse,
)
async def get_user_leg_map_by_time_period(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> str:
    return get_leg_map_page_by_user_id(
        get_network(),
        get_db_connection(),
        user_id,
        get_train_operator_brand_colour,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/years/{year}",
    summary="Get user train leg map for a time period",
    response_class=HTMLResponse,
)
async def get_user_leg_map_by_year(user_id: int, year: int) -> str:
    return get_leg_map_page_by_user_id(
        get_network(),
        get_db_connection(),
        user_id,
        get_train_operator_brand_colour,
        start_date=datetime(year, 1, 1),
        end_date=datetime(year, 12, 31),
    )

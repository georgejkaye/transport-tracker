from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from api.api.lifespan import get_db_connection
from api.db.train.stats import Stats, get_train_stats

router = APIRouter(prefix="/stats", tags=["users/train/stats"])


@router.get("", summary="Get train stats across a time period")
async def get_train_stats_in_range(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Stats:
    try:
        return get_train_stats(
            get_db_connection(), user_id, start_date, end_date
        )
    except RuntimeError:
        raise HTTPException(500, "Could not get stats")


@router.get("/years/{year}", summary="Get train stats across a year")
async def get_train_stats_from_year(
    user_id: int,
    year: int,
) -> Stats:
    try:
        return get_train_stats(
            get_db_connection(),
            user_id,
            datetime(year, 1, 1),
            datetime(year, 12, 31),
        )
    except RuntimeError:
        raise HTTPException(500, "Could not get stats")

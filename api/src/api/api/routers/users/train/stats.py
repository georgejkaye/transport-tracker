from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException

from api.data.stats import Stats, get_train_stats
from api.utils.database import connect_with_env


router = APIRouter(prefix="/stats", tags=["users/train/stats"])


@router.get("", summary="Get train stats across a time period")
async def get_train_stats_in_range(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Stats:
    with connect_with_env() as conn:
        try:
            return get_train_stats(conn, start_date, end_date)
        except RuntimeError:
            raise HTTPException(500, "Could not get stats")


@router.get("/year/{year}", summary="Get train stats across a year")
async def get_train_stats_from_year(
    user_id: int,
    year: int,
) -> Stats:
    with connect_with_env() as conn:
        try:
            return get_train_stats(
                conn, datetime(year, 1, 1), datetime(year, 12, 31)
            )
        except RuntimeError:
            raise HTTPException(500, "Could not get stats")

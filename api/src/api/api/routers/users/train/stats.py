from datetime import datetime

from fastapi import APIRouter, HTTPException

from api.api.lifespan import get_db_connection
from api.classes.train.stats import TrainStats
from api.stats.train import get_train_stats

router = APIRouter(prefix="/stats", tags=["users/train/stats"])


@router.get("", summary="Get train stats across a time period")
async def get_train_stats_in_range(
    user_id: int,
    start_date: datetime,
    end_date: datetime,
    rows_to_return: int = 5,
    operators_by_brands: bool = True,
) -> TrainStats:
    try:
        stats = get_train_stats(
            get_db_connection(),
            user_id,
            start_date,
            end_date,
            rows_to_return,
            operators_by_brands,
        )
        if stats is not None:
            return stats
        raise HTTPException(500, "Could not get stats")
    except RuntimeError:
        raise HTTPException(500, "Could not get stats")


@router.get("/years/{year}", summary="Get train stats across a time period")
async def get_train_stats_in_year(
    user_id: int,
    year: int,
    rows_to_return: int = 5,
    operators_by_brands: bool = True,
) -> TrainStats:
    try:
        stats = get_train_stats(
            get_db_connection(),
            user_id,
            datetime(year, 1, 1),
            datetime(year + 1, 1, 1),
            rows_to_return,
            operators_by_brands,
        )
        if stats is not None:
            return stats
        raise HTTPException(500, "Could not get stats")
    except RuntimeError:
        raise HTTPException(500, "Could not get stats")

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from api.api.lifespan import (
    get_db_connection,
    get_network,
)
from api.api.pagination import Page
from api.classes.network.geometry import TrainLegGeometry
from api.db.functions.select.train.leg import (
    select_train_leg_points_by_user_id_fetchall,
)
from api.db.types.user.train.leg import TransportUserTrainLegOutData
from api.network.map import get_train_leg_geometries_for_leg_points
from api.transform.train.legs import get_user_train_legs_in_range

router = APIRouter(prefix="/legs", tags=["users/train/legs"])


@router.get("", summary="Get user train legs across a time period")
async def get_user_legs_by_time_period(
    user_id: int,
    page_size: int = 10,
    page_no: int = 0,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    descending: bool = True,
) -> Page[TransportUserTrainLegOutData]:
    page = get_user_train_legs_in_range(
        get_db_connection(),
        user_id,
        page_size,
        page_no,
        start_date,
        end_date,
        descending,
    )
    if page is None:
        raise HTTPException(
            404, f"Could not get page {page_no} for user {user_id}"
        )
    return page


@router.get("/years/{year}", summary="Get user train legs across a year")
async def get_user_legs_by_year(
    user_id: int,
    year: int,
    page_size: int = 10,
    page_no: int = 0,
    descending: bool = True,
) -> Page[TransportUserTrainLegOutData]:
    page = get_user_train_legs_in_range(
        get_db_connection(),
        user_id,
        page_size,
        page_no,
        datetime(year, 1, 1),
        datetime(year + 1, 1, 1),
        descending,
    )
    if page is None:
        raise HTTPException(
            404, f"Could not get page {page_no} for user {user_id}"
        )
    return page


@router.get("/geometries", summary="Get train leg geometries for user")
async def get_train_geometries_for_user(
    user_id: int, start_date: datetime, end_date: datetime
) -> list[TrainLegGeometry]:
    legs = select_train_leg_points_by_user_id_fetchall(
        get_db_connection(), user_id, start_date, end_date
    )
    return get_train_leg_geometries_for_leg_points(get_network(), legs)


@router.get(
    "/geometries/years/{year}",
    summary="Get train leg geometries for user in a year",
)
async def get_train_geometries_for_user_year(
    user_id: int, year: int
) -> list[TrainLegGeometry]:
    legs = select_train_leg_points_by_user_id_fetchall(
        get_db_connection(),
        user_id,
        datetime(year, 1, 1),
        datetime(year + 1, 1, 1),
    )
    return get_train_leg_geometries_for_leg_points(get_network(), legs)

from datetime import datetime
from typing import Optional

from fastapi import APIRouter

from api.api.lifespan import (
    get_db_connection,
)
from api.db.functions.select.train.leg import (
    select_train_leg_points_by_user_id_fetchall,
)
from api.db.functions.select.train.user import (
    select_transport_user_train_leg_by_user_id_fetchall,
)
from api.db.types.train.leg import TrainLegPointsOutData
from api.db.types.user.train.leg import TransportUserTrainLegOutData

router = APIRouter(prefix="/legs", tags=["users/train/legs"])


@router.get("", summary="Get user train legs across a time period")
async def get_user_legs_by_time_period(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[TransportUserTrainLegOutData]:
    return select_transport_user_train_leg_by_user_id_fetchall(
        get_db_connection(),
        user_id,
        start_date,
        end_date,
    )


@router.get("/years/{year}", summary="Get user train legs across a year")
async def get_user_legs_by_year(
    user_id: int, year: int
) -> list[TransportUserTrainLegOutData]:
    return select_transport_user_train_leg_by_user_id_fetchall(
        get_db_connection(),
        user_id,
        datetime(year, 1, 1),
        datetime(year, 12, 31),
    )


@router.get("/geometries", summary="Get train leg geometries for user")
async def get_train_geometries_for_user(
    user_id: int, start_date: datetime, end_date: datetime
) -> list[TrainLegPointsOutData]:
    return select_train_leg_points_by_user_id_fetchall(
        get_db_connection(), user_id, start_date, end_date
    )


@router.get(
    "/geometries/years/{year}",
    summary="Get train leg geometries for user in a year",
)
async def get_train_geometries_for_user_year(
    user_id: int, year: int
) -> list[TrainLegPointsOutData]:
    return select_train_leg_points_by_user_id_fetchall(
        get_db_connection(),
        user_id,
        datetime(year, 1, 1),
        datetime(year, 12, 31),
    )

from datetime import datetime
from typing import Optional

from fastapi import APIRouter

from api.api.lifespan import (
    get_db_connection,
    get_network,
)
from api.classes.network.geometry import TrainLegGeometry
from api.classes.users.train.legs import DbTransportUserTrainLegOutData
from api.db.train.legs import select_train_leg_points_by_user_id
from api.db.users.train.legs import select_transport_user_train_leg_by_user_id
from api.network.map import (
    get_train_leg_geometries_for_leg_points,
)

router = APIRouter(prefix="/legs", tags=["users/train/legs"])


@router.get("", summary="Get user train legs across a time period")
async def get_user_legs_by_time_period(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[DbTransportUserTrainLegOutData]:
    return select_transport_user_train_leg_by_user_id(
        get_db_connection(),
        user_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/years/{year}", summary="Get user train legs across a year")
async def get_user_legs_by_year(
    user_id: int, year: int
) -> list[DbTransportUserTrainLegOutData]:
    return select_transport_user_train_leg_by_user_id(
        get_db_connection(),
        user_id,
        start_date=datetime(year, 1, 1),
        end_date=datetime(year, 12, 31),
    )


@router.get("/geometries", summary="Get train leg geometries for user")
async def get_train_geometries_for_user(
    user_id: int, start_date: datetime, end_date: datetime
) -> list[TrainLegGeometry]:
    legs = select_train_leg_points_by_user_id(
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
    legs = select_train_leg_points_by_user_id(
        get_db_connection(),
        user_id,
        datetime(year, 1, 1),
        datetime(year, 12, 31),
    )
    return get_train_leg_geometries_for_leg_points(get_network(), legs)

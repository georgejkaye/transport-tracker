from datetime import datetime
from typing import Optional

from fastapi import APIRouter

from api.classes.users.train.legs import DbTransportUserTrainLegOutData
from api.db.users.train.legs import select_transport_user_train_leg_by_user_id
from api.utils.database import connect_with_env

router = APIRouter(prefix="/legs", tags=["users/train/legs"])


@router.get("", summary="Get user train legs across a time period")
async def get_user_legs_by_time_period(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[DbTransportUserTrainLegOutData]:
    with connect_with_env() as conn:
        return select_transport_user_train_leg_by_user_id(
            conn, user_id, search_start=start_date, search_end=end_date
        )


@router.get("/years/{year}", summary="Get user train legs across a year")
async def get_user_legs_by_year(
    user_id: int, year: int
) -> list[DbTransportUserTrainLegOutData]:
    with connect_with_env() as conn:
        return select_transport_user_train_leg_by_user_id(
            conn,
            user_id,
            search_start=datetime(year, 1, 1),
            search_end=datetime(year, 12, 31),
        )

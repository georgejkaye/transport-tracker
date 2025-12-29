from datetime import datetime
from typing import Optional

from api.db.functions.select.train.user.operator import (
    select_transport_user_train_brand_by_user_id_and_brand_id_fetchone,
)
from fastapi import APIRouter, HTTPException

from api.api.lifespan import get_db_connection
from api.db.types.user.train.operator import TransportUserTrainOperatorOutData

router = APIRouter(prefix="/brands", tags=["users/train/operators"])


@router.get("/{brand_id}", summary="Get brand data for a user")
def get_user_brand(
    user_id: int,
    brand_id: int,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
) -> Optional[TransportUserTrainOperatorOutData]:
    brand = select_transport_user_train_brand_by_user_id_and_brand_id_fetchone(
        get_db_connection(),
        user_id,
        brand_id,
        search_start,
        search_end,
    )
    if brand is None:
        raise HTTPException(
            404,
            f"Could not get brand id {brand_id} for user id {user_id}",
        )
    return brand


@router.get("/{brand_id}/years/{year}", summary="Get brand data for a user")
def get_user_brand_by_year(
    user_id: int, brand_id: int, year: int
) -> Optional[TransportUserTrainOperatorOutData]:
    brand = select_transport_user_train_brand_by_user_id_and_brand_id_fetchone(
        get_db_connection(),
        user_id,
        brand_id,
        datetime(year, 1, 1),
        datetime(year + 1, 1, 1),
    )
    if brand is None:
        raise HTTPException(
            404,
            f"Could not get brand id {brand_id} for user id {user_id}",
        )
    return brand

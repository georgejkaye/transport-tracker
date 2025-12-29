from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from api.api.lifespan import get_db_connection
from api.db.functions.select.train.user.operator import (
    select_transport_user_train_operator_by_user_id_and_operator_id_fetchone,
    select_transport_user_train_operator_by_user_id_fetchall,
)
from api.db.types.user.train.operator import (
    TransportUserTrainOperatorHighOutData,
    TransportUserTrainOperatorOutData,
)

router = APIRouter(prefix="/operators", tags=["users/train/operators"])


@router.get("/", summary="Get all operator data for a user")
def get_user_operators(
    user_id: int,
    by_brands: bool = True,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
) -> list[TransportUserTrainOperatorHighOutData]:
    operators = select_transport_user_train_operator_by_user_id_fetchall(
        get_db_connection(), user_id, by_brands, search_start, search_end
    )
    return operators


@router.get(
    "/years/{year}", summary="Get all operator data for a user in a given year"
)
def get_user_operators_by_year(
    user_id: int, year: int, by_brands: bool = True
) -> list[TransportUserTrainOperatorHighOutData]:
    operators = select_transport_user_train_operator_by_user_id_fetchall(
        get_db_connection(),
        user_id,
        by_brands,
        datetime(year, 1, 1),
        datetime(year + 1, 1, 1),
    )
    return operators


@router.get("/{operator_id}", summary="Get operator data for a user")
def get_user_operator(
    user_id: int,
    operator_id: int,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
) -> Optional[TransportUserTrainOperatorOutData]:
    operator = select_transport_user_train_operator_by_user_id_and_operator_id_fetchone(
        get_db_connection(),
        user_id,
        operator_id,
        search_start,
        search_end,
    )
    if operator is None:
        raise HTTPException(
            404,
            f"Could not get operator id {operator_id} for user id {user_id}",
        )
    return operator


@router.get(
    "/{operator_id}/years/{year}",
    summary="Get operator data for a user in a given year",
)
def get_user_operator_by_year(
    user_id: int, operator_id: int, year: int
) -> Optional[TransportUserTrainOperatorOutData]:
    operator = select_transport_user_train_operator_by_user_id_and_operator_id_fetchone(
        get_db_connection(),
        user_id,
        operator_id,
        datetime(year, 1, 1),
        datetime(year + 1, 1, 1),
    )
    if operator is None:
        raise HTTPException(
            404,
            f"Could not get operator id {operator_id} for user id {user_id}",
        )
    return operator

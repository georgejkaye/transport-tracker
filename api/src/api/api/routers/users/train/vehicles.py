from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from api.api.lifespan import get_db_connection
from api.db.functions.select.train.user.vehicle import (
    select_transport_user_train_stock_class_by_user_id_and_class_fetchone,
    select_transport_user_train_stock_class_by_user_id_fetchall,
    select_transport_user_train_stock_unit_by_user_id_and_number_fetchone,
    select_transport_user_train_stock_unit_by_user_id_fetchall,
)
from api.db.types.user.train.vehicle import (
    TransportUserTrainClassHighOutData,
    TransportUserTrainClassOutData,
    TransportUserTrainUnitHighOutData,
    TransportUserTrainUnitOutData,
)

router = APIRouter(prefix="/vehicles", tags=["users/train/vehicles"])


@router.get("/classes", summary="Get stock class data for a user")
async def get_train_classes(
    user_id: int,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
) -> list[TransportUserTrainClassHighOutData]:
    class_data = select_transport_user_train_stock_class_by_user_id_fetchall(
        get_db_connection(), user_id, search_start, search_end
    )
    return class_data


@router.get(
    "/classes/years/{year}",
    summary="Get stock class data for a user in a given year",
)
async def get_train_classes_by_year(
    user_id: int, year: int
) -> list[TransportUserTrainClassHighOutData]:
    class_data = select_transport_user_train_stock_class_by_user_id_fetchall(
        get_db_connection(),
        user_id,
        datetime(year, 1, 1),
        datetime(year + 1, 1, 1),
    )
    return class_data


@router.get(
    "/classes/{class_number}",
    summary="Get stock class data for a user and a particular class number",
)
async def get_train_class(
    user_id: int,
    class_number: int,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
) -> TransportUserTrainClassOutData:
    class_data = (
        select_transport_user_train_stock_class_by_user_id_and_class_fetchone(
            get_db_connection(), user_id, class_number, search_start, search_end
        )
    )
    if class_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Train class {class_number} not found for user {user_id}",
        )
    return class_data


@router.get(
    "/classes/{class_number}/years/{year}",
    summary="Get stock class data for a user and a particular class number in a given year",
)
async def get_train_class_by_year(
    user_id: int, class_number: int, year: int
) -> TransportUserTrainClassOutData:
    class_data = (
        select_transport_user_train_stock_class_by_user_id_and_class_fetchone(
            get_db_connection(),
            user_id,
            class_number,
            datetime(year, 1, 1),
            datetime(year + 1, 1, 1),
        )
    )
    if class_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Train class {class_number} not found for user {user_id}",
        )
    return class_data


@router.get("/units", summary="Get stock unit data for a user")
async def get_train_units(
    user_id: int,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
) -> list[TransportUserTrainUnitHighOutData]:
    unit_data = select_transport_user_train_stock_unit_by_user_id_fetchall(
        get_db_connection(), user_id, search_start, search_end
    )
    return unit_data


@router.get(
    "/units/years/{year}",
    summary="Get stock unit data for a user in a given year",
)
async def get_train_units_by_year(
    user_id: int, year: int
) -> list[TransportUserTrainUnitHighOutData]:
    unit_data = select_transport_user_train_stock_unit_by_user_id_fetchall(
        get_db_connection(),
        user_id,
        datetime(year, 1, 1),
        datetime(year + 1, 1, 1),
    )
    return unit_data


@router.get(
    "/units/{unit_number}",
    summary="Get stock unit data for a user and a particular unit number",
)
async def get_train_unit(
    user_id: int,
    unit_number: int,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
) -> TransportUserTrainUnitOutData:
    unit_data = (
        select_transport_user_train_stock_unit_by_user_id_and_number_fetchone(
            get_db_connection(), user_id, unit_number, search_start, search_end
        )
    )
    if unit_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Train unit {unit_number} not found for user {user_id}",
        )
    return unit_data


@router.get(
    "/units/{unit_number}/years/{year}",
    summary="Get stock unit data for a user and a particular unit number in a given year",
)
async def get_train_unit_by_year(
    user_id: int, unit_number: int, year: int
) -> TransportUserTrainUnitOutData:
    unit_data = (
        select_transport_user_train_stock_unit_by_user_id_and_number_fetchone(
            get_db_connection(),
            user_id,
            unit_number,
            datetime(year, 1, 1),
            datetime(year + 1, 1, 1),
        )
    )
    if unit_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Train unit {unit_number} not found for user {user_id}",
        )
    return unit_data

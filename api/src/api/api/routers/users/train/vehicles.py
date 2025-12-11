from fastapi import APIRouter, HTTPException

from api.api.lifespan import get_db_connection
from api.db.functions.select.train.user import (
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


@router.get("/class", summary="Get stock class data for a user")
async def get_train_classes(
    user_id: int,
) -> list[TransportUserTrainClassHighOutData]:
    class_data = select_transport_user_train_stock_class_by_user_id_fetchall(
        get_db_connection(), user_id
    )
    return class_data


@router.get(
    "/class/{class_number}",
    summary="Get stock class data for a user and a particular class number",
)
async def get_train_class(
    user_id: int, class_number: int
) -> TransportUserTrainClassOutData:
    class_data = (
        select_transport_user_train_stock_class_by_user_id_and_class_fetchone(
            get_db_connection(), user_id, class_number
        )
    )
    if class_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Train class {class_number} not found for user {user_id}",
        )
    return class_data


@router.get("/unit", summary="Get stock unit data for a user")
async def get_train_units(
    user_id: int,
) -> list[TransportUserTrainUnitHighOutData]:
    unit_data = select_transport_user_train_stock_unit_by_user_id_fetchall(
        get_db_connection(), user_id
    )
    return unit_data


@router.get(
    "/unit/{unit_number}",
    summary="Get stock unit data for a user and a particular unit number",
)
async def get_train_unit(
    user_id: int, unit_number: int
) -> TransportUserTrainUnitOutData:
    unit_data = (
        select_transport_user_train_stock_unit_by_user_id_and_number_fetchone(
            get_db_connection(), user_id, unit_number
        )
    )
    if unit_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Train unit {unit_number} not found for user {user_id}",
        )
    return unit_data

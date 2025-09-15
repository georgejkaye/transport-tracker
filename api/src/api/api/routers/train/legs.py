from fastapi import APIRouter, HTTPException

from api.api.network import network
from api.classes.network.geometry import TrainLegGeometry
from api.classes.train.leg import DbTrainLegOutData
from api.db.train.legs import select_train_leg_by_id, select_train_legs_by_ids
from api.network.map import get_leg_geometries
from api.utils.database import connect_with_env

router = APIRouter(prefix="/legs", tags=["train/legs"])


@router.get("/{leg_id}", summary="Get train leg with id")
async def get_leg(train_leg_id: int) -> DbTrainLegOutData:
    with connect_with_env() as conn:
        leg = select_train_leg_by_id(conn, train_leg_id)
    if leg is None:
        raise HTTPException(404, f"Could not find leg id {train_leg_id}")
    return leg


@router.get("/geometries", summary="Get geometries for legs")
async def get_geometries_for_legs(
    train_leg_ids: list[int],
) -> list[TrainLegGeometry]:
    with connect_with_env() as conn:
        legs = select_train_legs_by_ids(conn, train_leg_ids)
        return get_leg_geometries(conn, network, legs)

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from api.api.lifespan import (
    get_db_connection,
    get_network,
    get_train_operator_brand_colour,
)
from api.classes.network.geometry import TrainLegGeometry
from api.classes.train.legs import DbTrainLegOutData
from api.db.train.legs import (
    select_train_leg_by_id,
    select_train_leg_points_by_leg_id,
    select_train_leg_points_by_leg_ids,
)
from api.network.map import (
    get_leg_map_page_by_leg_id,
    get_train_leg_geometries_for_leg_points,
    get_train_leg_geometry_for_leg_points,
)

router = APIRouter(prefix="/legs", tags=["train/legs"])


@router.get("/{leg_id}", summary="Get train leg with id")
async def get_leg(leg_id: int) -> DbTrainLegOutData:
    leg = select_train_leg_by_id(get_db_connection(), leg_id)
    if leg is None:
        raise HTTPException(404, f"Could not find leg id {leg_id}")
    return leg


@router.get("/geometries/{leg_id}", summary="Get geometries for leg")
async def get_geometries_for_leg(leg_id: int) -> TrainLegGeometry:
    leg_points = select_train_leg_points_by_leg_id(get_db_connection(), leg_id)
    if leg_points is None:
        raise HTTPException(404, f"Could not find train leg id {leg_id}")
    train_leg_geometry = get_train_leg_geometry_for_leg_points(
        get_network(), leg_points
    )
    if train_leg_geometry is None:
        raise HTTPException(404, f"Could not find geometry for leg id {leg_id}")
    return train_leg_geometry


@router.get("/geometries", summary="Get geometries for legs")
async def get_geometries_for_legs(
    train_leg_ids: list[int],
) -> list[TrainLegGeometry]:
    legs = select_train_leg_points_by_leg_ids(
        get_db_connection(), train_leg_ids
    )
    return get_train_leg_geometries_for_leg_points(get_network(), legs)


@router.get(
    "/maps/{leg_id}",
    summary="Get a map for a particular train leg",
    response_class=HTMLResponse,
)
async def get_map_by_train_leg(leg_id: int) -> str:
    return get_leg_map_page_by_leg_id(
        get_db_connection(),
        get_network(),
        leg_id,
        get_train_operator_brand_colour,
    )

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException

from api.db.train.leg import select_legs
from api.utils.database import connect_with_env
from api.api.network import network
from api.network.map import (
    ShortLegWithGeometry,
    get_short_legs_with_geometries,
    short_legs_to_short_legs_with_geometries,
)

router = APIRouter(prefix="/legs", tags=["users/train/legs"])


@router.get("", summary="Get train legs across a time period")
async def get_legs(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    fetch_geometries: bool = False,
) -> list[ShortLegWithGeometry]:
    with connect_with_env() as conn:
        legs = select_legs(
            conn, user_id, search_start=start_date, search_end=end_date
        )
        if fetch_geometries:
            legs_with_geometries = get_short_legs_with_geometries(
                conn, network, legs
            )
        else:
            legs_with_geometries = short_legs_to_short_legs_with_geometries(
                legs
            )
        return legs_with_geometries


@router.get("/years/{year}", summary="Get train legs across a year")
async def get_legs_from_year(
    user_id: int, year: int, fetch_geometries: bool = False
) -> list[ShortLegWithGeometry]:
    with connect_with_env() as conn:
        legs = select_legs(
            conn,
            user_id,
            search_start=datetime(year, 1, 1),
            search_end=datetime(year, 12, 31),
        )
        if fetch_geometries:
            legs_with_geometries = get_short_legs_with_geometries(
                conn, network, legs
            )
        else:
            legs_with_geometries = short_legs_to_short_legs_with_geometries(
                legs
            )
        return legs_with_geometries


@router.get("/{leg_id}", summary="Get particular train leg")
async def get_leg(
    user_id: int, leg_id: int, fetch_geometries: bool = False
) -> ShortLegWithGeometry:
    with connect_with_env() as conn:
        legs = select_legs(conn, user_id, search_leg_id=leg_id)
        if fetch_geometries:
            legs_with_geometries = get_short_legs_with_geometries(
                conn, network, legs
            )
        else:
            legs_with_geometries = short_legs_to_short_legs_with_geometries(
                legs
            )
        if len(legs) != 1:
            raise HTTPException(status_code=404, detail="Leg not found")
        return legs_with_geometries[0]

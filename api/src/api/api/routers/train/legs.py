from datetime import datetime
from typing import Optional
from urllib import request
from api.network.map import (
    ShortLegWithGeometry,
    get_short_legs_with_geometries,
    short_legs_to_short_legs_with_geometries,
)
from fastapi import APIRouter, HTTPException

from api.data.leg import ShortLeg, select_legs
from api.utils.database import connect

from api.api.network import network

router = APIRouter(prefix="/legs", tags=["train/legs"])


@router.get("", summary="Get train legs across a time period")
async def get_legs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    fetch_geometries: bool = False,
) -> list[ShortLegWithGeometry]:
    with connect() as (conn, _):
        legs = select_legs(conn, search_start=start_date, search_end=end_date)
        if fetch_geometries:
            legs = get_short_legs_with_geometries(conn, network, legs)
        else:
            legs = short_legs_to_short_legs_with_geometries(legs)
        return legs


@router.get("/year/{year}", summary="Get train legs across a year")
async def get_legs_from_year(
    year: int, fetch_geometries: bool = False
) -> list[ShortLegWithGeometry]:
    with connect() as (conn, _):
        legs = select_legs(
            conn,
            search_start=datetime(year, 1, 1),
            search_end=datetime(year, 12, 31),
        )
        if fetch_geometries:
            legs = get_short_legs_with_geometries(conn, network, legs)
        else:
            legs = short_legs_to_short_legs_with_geometries(legs)
        return legs


@router.get("/{leg_id}", summary="Get particular train leg")
async def get_leg(
    leg_id: int, fetch_geometries: bool = False
) -> ShortLegWithGeometry:
    with connect() as (conn, _):
        legs = select_legs(conn, search_leg_id=leg_id)
        if fetch_geometries:
            legs = get_short_legs_with_geometries(conn, network, legs)
        else:
            legs = short_legs_to_short_legs_with_geometries(legs)
        if len(legs) != 1:
            raise HTTPException(status_code=404, detail="Leg not found")
        return legs[0]

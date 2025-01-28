from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException

from api.data.leg import ShortLeg, select_legs
from api.utils.database import connect

router = APIRouter(prefix="/legs", tags=["train/legs"])


@router.get("", summary="Get train legs across a time period")
async def get_legs(
    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
) -> list[ShortLeg]:
    with connect() as (conn, _):
        legs = select_legs(conn, start_date, end_date)
        return legs


@router.get("/year/{year}", summary="Get train legs across a year")
async def get_legs_from_year(year: int) -> list[ShortLeg]:
    with connect() as (conn, _):
        legs = select_legs(conn, datetime(year, 1, 1), datetime(year, 12, 31))
        return legs


@router.get("/{leg_id}", summary="Get particular train leg")
async def get_leg(leg_id: int) -> ShortLeg:
    with connect() as (conn, _):
        legs = select_legs(conn, search_leg_id=leg_id)
        if len(legs) != 1:
            raise HTTPException(status_code=404, detail="Leg not found")
        return legs[0]

from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from api.utils.database import connect_with_env
from api.classes.network.map import LegLine, StationInfo
from api.db.train.points import get_station_points_from_crses
from api.db.train.stations import select_station_from_crs
from api.network.map import (
    LegData,
    get_leg_map,
    get_leg_map_page_from_leg_data,
)
from api.network.pathfinding import find_shortest_path_between_stations
from api.api.network import network

router = APIRouter(prefix="/train", tags=["utils/train"])


@router.get(
    "/route",
    summary="Get route between two train stations",
    response_class=HTMLResponse,
)
async def get_route_between_stations(
    from_crs: str,
    to_crs: str,
    from_platform: Optional[str] = None,
    to_platform: Optional[str] = None,
) -> str:
    with connect_with_env() as conn:
        from_station = select_station_from_crs(conn, from_crs)
        if from_station is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not find station for code {from_crs}",
            )
        to_station = select_station_from_crs(conn, to_crs)
        if to_station is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not find station for code {to_crs}",
            )
        station_points = get_station_points_from_crses(
            conn, [(from_crs, from_platform), (to_crs, to_platform)]
        )
        path = find_shortest_path_between_stations(
            network,
            from_crs,
            from_platform,
            to_crs,
            to_platform,
            station_points,
        )
        if path is None:
            raise HTTPException(
                status_code=404,
                detail="Could not find a route between these stations",
            )
        (source_point, target_point, linestring) = path
        return get_leg_map(
            [],
            [
                LegLine(
                    from_station.name,
                    to_station.name,
                    [source_point, target_point],
                    linestring,
                    "#000000",
                    0,
                    0,
                )
            ],
            StationInfo(False),
        )


@router.post(
    "/data",
    summary="Get map of train legs from a data set",
    response_class=HTMLResponse,
)
async def get_train_map_from_data(legs: list[LegData]) -> str:
    return get_leg_map_page_from_leg_data(network, legs)

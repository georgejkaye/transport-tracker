from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from api.api.lifespan import get_db_connection, get_network
from api.classes.network.map import (
    LegLine,
    MarkerTextParams,
)
from api.classes.train.station import DbTrainStationPointPointsOutData
from api.network.map import (
    LegData,
    get_leg_map,
    get_leg_map_page_from_leg_data,
)
from api.network.pathfinding import find_shortest_path_between_network_nodes

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
    station_points = select_train_station_points_by_crses(
        get_db_connection(), [from_crs, to_crs]
    )
    if len(station_points) != 2:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find station for code {from_crs} or {to_crs}",
        )
    from_points = [
        DbTrainStationPointPointsOutData(station_points[0], platform_point)
        for platform_point in station_points[0].platform_points
    ]
    to_points = [
        DbTrainStationPointPointsOutData(station_points[-1], platform_point)
        for platform_point in station_points[-1].platform_points
    ]
    path = find_shortest_path_between_network_nodes(
        get_network(), from_points, to_points
    )
    if path is None:
        raise HTTPException(
            status_code=404,
            detail="Could not find a route between these stations",
        )
    return get_leg_map(
        [],
        [
            LegLine(
                path.source.station.station_name,
                path.target.station.station_name,
                [path.source, path.target],
                path.line,
                "#000000",
                0,
                0,
            )
        ],
        MarkerTextParams(False),
    )


@router.post(
    "/data",
    summary="Get map of train legs from a data set",
    response_class=HTMLResponse,
)
async def get_train_map_from_data(legs: list[LegData]) -> str:
    return get_leg_map_page_from_leg_data(
        get_db_connection(), get_network(), legs
    )

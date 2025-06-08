from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from psycopg import Connection
from shapely import Point

from api.utils.database import register_type
from api.data.train.stations import TrainLegCallStationInData


@dataclass
class PointTimes:
    plan_dep: Optional[datetime]
    plan_arr: Optional[datetime]
    act_dep: Optional[datetime]
    act_arr: Optional[datetime]


@dataclass
class StationPoint:
    crs: str
    name: str
    platform: Optional[str]
    point: Point
    call: Optional[PointTimes] = None


@dataclass
class StationLocation:
    platform: Optional[str]
    point: Point


@dataclass
class StationAndPlatform:
    crs: str
    platform: Optional[str]


@dataclass
class StationPointCrsSearchResult:
    crs: str
    name: str
    station_points: list[StationLocation]


def get_station_point_from_crs_and_platform(
    conn: Connection, station_crs: str, platform: Optional[str]
) -> Optional[Point]:
    row = conn.execute(
        "SELECT * FROM GetStationPoint(%s, %s)", [station_crs.upper(), platform]
    ).fetchone()
    if row is None:
        return None
    return Point(row[1], row[0])


def string_of_station_point(station_point: StationPoint) -> str:
    if station_point.platform is None:
        platform_string = ""
    else:
        platform_string = f": platform {station_point.platform}"
    return f"{station_point.name}{platform_string}"


def register_station_and_points(
    station_crs: str, station_name: str, station_points: list[StationLocation]
) -> StationPointCrsSearchResult:
    return StationPointCrsSearchResult(
        station_crs, station_name, station_points
    )


@dataclass
class StationPointNameSearchResult:
    crs: str
    name: str
    search_name: str
    station_points: list[StationLocation]


def register_station_name_and_points(
    station_crs: str,
    station_name: str,
    search_name: str,
    station_points: list[StationLocation],
) -> StationPointNameSearchResult:
    return StationPointNameSearchResult(
        station_crs, station_name, search_name, station_points
    )


def get_station_point_dict(
    rows: (
        list[StationPointCrsSearchResult] | list[StationPointNameSearchResult]
    ),
) -> dict[str, dict[Optional[str], StationPoint]]:
    station_point_dict = {}
    for row in rows:
        station_point_dict[row.crs] = {}
        for point in row.station_points:
            station_point_dict[row.crs][point.platform] = StationPoint(
                row.crs, row.name, point.platform, point.point
            )
    return station_point_dict


def register_station_latlon(
    platform: str, latitude: float, longitude: float
) -> StationLocation:
    return StationLocation(platform, Point(longitude, latitude))


def get_station_points(
    conn: Connection,
) -> dict[str, dict[Optional[str], StationPoint]]:
    register_type(conn, "StationLatLon", register_station_latlon)
    rows = conn.execute("SELECT GetStationPoints()").fetchall()
    return get_station_point_dict([row[0] for row in rows])


def get_station_points_from_crses(
    conn: Connection, stations: list[tuple[str, Optional[str]]]
) -> dict[str, dict[Optional[str], StationPoint]]:
    register_type(conn, "StationLatLon", register_station_latlon)
    register_type(conn, "StationAndPoints", register_station_and_points)
    rows = conn.execute(
        "SELECT GetStationPointsFromCrses(%s::StationCrsAndPlatform[])",
        [stations],
    ).fetchall()
    return get_station_point_dict([row[0] for row in rows])


def get_station_points_from_names(
    conn: Connection, stations: list[tuple[str, Optional[str]]]
) -> tuple[
    dict[str, TrainLegCallStationInData],
    dict[str, dict[Optional[str], StationPoint]],
]:
    register_type(conn, "StationLatLon", register_station_latlon)
    register_type(
        conn, "StationNameAndPoints", register_station_name_and_points
    )
    rows = conn.execute(
        "SELECT GetStationPointsFromNames(%s::StationNameAndPlatform[])",
        [stations],
    ).fetchall()
    name_to_station_dict = {}
    for row in rows:
        row = row[0]
        name_to_station_dict[row.search_name] = TrainLegCallStationInData(
            row.name, row.crs
        )
    return (
        name_to_station_dict,
        get_station_point_dict([row[0] for row in rows]),
    )


def get_relevant_station_points(
    station_crs: str,
    platform: Optional[str],
    station_points: dict[str, dict[Optional[str], StationPoint]],
) -> list[StationPoint]:
    crs_points = station_points[station_crs]
    if platform is None or crs_points.get(platform) is None:
        return [crs_points[key] for key in crs_points.keys()]
    return [crs_points[platform]]

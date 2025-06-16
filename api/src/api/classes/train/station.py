from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from psycopg import Connection
from shapely import Point

from api.utils.database import register_type
from api.utils.times import get_hourmin_string
from api.classes.train.operators import BrandData, OperatorData


@dataclass
class TrainStation:
    name: str
    crs: str
    operator: int
    brand: Optional[int]


@dataclass
class TrainStationIdentifiers:
    crs: str
    name: str


@dataclass
class TrainServiceAtStation:
    id: str
    headcode: str
    run_date: datetime
    origins: list[TrainStationIdentifiers]
    destinations: list[TrainStationIdentifiers]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    operator_code: str
    brand_code: str


def get_multiple_short_station_string(
    locs: list[TrainStationIdentifiers],
) -> str:
    string = ""
    for i, loc in enumerate(locs):
        if i == 0:
            string = loc.name
        else:
            string = f"{string} and {loc.name}"
    return string


def short_string_of_service_at_station(service: TrainServiceAtStation) -> str:
    return f"{service.headcode} {get_multiple_short_station_string(service.origins)} to {get_multiple_short_station_string(service.destinations)}"


def string_of_service_at_station(service: TrainServiceAtStation) -> str:
    return f"{service.headcode} {get_multiple_short_station_string(service.origins)} to {get_multiple_short_station_string(service.destinations)} plan {get_hourmin_string(service.plan_dep)} act {get_hourmin_string(service.act_dep)} ({service.operator_code})"


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


def register_station_data(
    station_crs: str, station_name: str
) -> TrainStationIdentifiers:
    return TrainStationIdentifiers(station_crs, station_name)


def register_short_train_station_types(conn: Connection) -> None:
    register_type(conn, "TrainStationOutData", register_station_data)


@dataclass
class LegAtStation:
    id: int
    platform: Optional[str]
    origin: TrainStationIdentifiers
    destination: TrainStationIdentifiers
    stop_time: datetime
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    calls_before: Optional[int]
    calls_after: Optional[int]
    operator: OperatorData
    brand: Optional[BrandData]


@dataclass
class StationData:
    name: str
    crs: str
    operator: OperatorData
    brand: Optional[BrandData]
    legs: list[LegAtStation]
    img: str
    starts: int
    finishes: int
    passes: int

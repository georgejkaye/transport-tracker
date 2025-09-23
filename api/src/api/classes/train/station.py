from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from psycopg import Connection
from shapely import Point

from api.classes.network.map import (
    LegLineCall,
    MarkerTextParams,
    MarkerTextValues,
    NetworkNode,
)
from api.classes.train.network import get_node_id_from_crs_and_platform
from api.classes.train.operators import BrandData, OperatorData
from api.utils.database import register_type
from api.utils.times import get_hourmin_string


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
class StationPoint(NetworkNode):
    crs: str
    platform: Optional[str]
    point: Point

    def get_id(self) -> int:
        return get_node_id_from_crs_and_platform(self.crs, self.platform)


@dataclass
class StationLocation:
    platform: Optional[str]
    point: Point


@dataclass
class StationAndPlatform:
    crs: str
    platform: Optional[str]

    def get_id(self) -> int:
        return get_node_id_from_crs_and_platform(self.crs, self.platform)


@dataclass
class StationPointCrsSearchResult:
    crs: str
    name: str
    station_points: list[StationLocation]


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


@dataclass
class DbTrainStationOutData:
    station_id: int
    station_name: str
    station_crs: str
    operator_id: int
    brand_id: Optional[int]


@dataclass
class DbTrainStationPointOutData:
    platform: Optional[str]
    latitude: Decimal
    longitude: Decimal


@dataclass
class DbTrainStationPointsOutData:
    station_id: int
    station_name: str
    station_crs: str
    search_name: str
    platform_points: list[DbTrainStationPointOutData]


def register_train_station_points_out_data(conn: Connection):
    register_type(
        conn, "train_station_point_out_data", DbTrainStationPointOutData
    )
    register_type(
        conn, "train_station_points_out_data", DbTrainStationPointsOutData
    )


@dataclass
class DbTrainStationLegPointsOutData:
    leg_stations: list[DbTrainStationPointsOutData]


def register_train_station_leg_points_out_data(conn: Connection):
    register_type(
        conn, "train_station_point_out_data", DbTrainStationPointOutData
    )
    register_type(
        conn, "train_station_points_out_data", DbTrainStationPointsOutData
    )
    register_type(
        conn,
        "train_station_leg_points_out_data",
        DbTrainStationLegPointsOutData,
    )


@dataclass
class DbTrainStationPointPointsOutData(LegLineCall):
    station: DbTrainStationPointsOutData
    point: DbTrainStationPointOutData

    def get_id(self) -> int:
        return get_node_id_from_crs_and_platform(
            self.station.station_crs, self.point.platform
        )

    def get_call_info_text(
        self, params: MarkerTextParams, values: MarkerTextValues
    ) -> str:
        if params.include_counts:
            count_string = f"""
                    <b>Boards:</b> {values.boards}<br/>
                    <b>Alights:</b> {values.alights}<br/>
                    <b>Calls:</b> {values.calls}
                """
        else:
            count_string = ""
        return f"<h1>{self.station.station_name} ({self.station.station_crs})</h1>{count_string}"

    def get_call_identifier(self) -> str:
        return self.station.station_crs

    def get_point(self) -> Point:
        return Point(float(self.point.latitude), float(self.point.longitude))

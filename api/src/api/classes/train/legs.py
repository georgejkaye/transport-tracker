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
)
from api.classes.train.association import AssociationType
from api.classes.train.network import get_node_id_from_crs_and_platform
from api.classes.train.service import (
    DbTrainAssociatedServiceInData,
    DbTrainCallInData,
    DbTrainServiceEndpointInData,
    DbTrainServiceInData,
    TrainServiceInData,
)
from api.classes.train.station import (
    TrainStationIdentifiers,
    get_multiple_short_station_string,
)
from api.classes.train.stock import StockReport
from api.utils.database import register_type
from api.utils.times import get_hourmin_string


@dataclass
class TrainLegCallCallInData:
    service_run_id: str
    service_run_date: datetime
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]


@dataclass
class TrainLegCallInData:
    station_crs: str
    station_name: str
    arr_call: Optional[TrainLegCallCallInData]
    dep_call: Optional[TrainLegCallCallInData]
    mileage: Optional[Decimal]
    association_type: Optional[AssociationType]


@dataclass
class TrainStockReportInData:
    stock_report: list[StockReport]
    start_crs: str
    start_call: TrainLegCallCallInData
    end_crs: str
    end_call: TrainLegCallCallInData
    mileage: Optional[Decimal]


@dataclass
class TrainLegInData:
    primary_service: TrainServiceInData
    calls: list[TrainLegCallInData]
    distance: Optional[Decimal]
    stock_reports: Optional[list[TrainStockReportInData]]


@dataclass
class TrainServiceAtStationToDestination:
    id: str
    headcode: str
    run_date: datetime
    origins: list[TrainStationIdentifiers]
    destinations: list[TrainStationIdentifiers]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    operator_code: str
    brand_code: str
    calls_to_destination: list[TrainLegCallInData]


def string_of_service_at_station_to_destination(
    service: TrainServiceAtStationToDestination,
) -> str:
    return f"{service.headcode} {get_multiple_short_station_string(service.origins)} to {get_multiple_short_station_string(service.destinations)} plan {get_hourmin_string(service.plan_dep)} act {get_hourmin_string(service.act_dep)} ({service.operator_code})"


###
# DB input
###

DbTrainLegCallInData = tuple[
    str,
    Optional[str],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[str],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[Decimal],
    Optional[int],
]

DbTrainStockSegmentInData = tuple[
    Optional[int],
    Optional[int],
    Optional[int],
    Optional[int],
    str,
    datetime,
    str,
    Optional[datetime],
    Optional[datetime],
    str,
    datetime,
    str,
    Optional[datetime],
    Optional[datetime],
]

DbTrainLegInData = tuple[
    list[DbTrainServiceInData],
    list[DbTrainServiceEndpointInData],
    list[DbTrainCallInData],
    list[DbTrainAssociatedServiceInData],
    list[DbTrainLegCallInData],
    Optional[list[DbTrainStockSegmentInData]],
    Optional[Decimal],
]


@dataclass
class InsertTrainLegResult:
    insert_train_leg: int


@dataclass
class DbTrainLegStationOutData:
    station_id: int
    station_crs: str
    station_name: str


def register_train_leg_station_out_data(conn: Connection) -> None:
    register_type(conn, "train_leg_station_out_data", DbTrainLegStationOutData)


@dataclass
class DbTrainLegOperatorOutData:
    operator_id: int
    operator_code: str
    operator_name: str


def register_train_leg_operator_out_data(conn: Connection) -> None:
    register_type(
        conn, "train_leg_operator_out_data", DbTrainLegOperatorOutData
    )


@dataclass
class DbTrainLegServiceOutData:
    service_id: int
    unique_identifier: str
    run_date: datetime
    headcode: str
    start_datetime: datetime
    origins: list[DbTrainLegStationOutData]
    destinations: list[DbTrainLegStationOutData]
    operator: DbTrainLegOperatorOutData
    brand: Optional[DbTrainLegOperatorOutData]


def register_train_leg_service_out_data(conn: Connection) -> None:
    register_type(conn, "train_leg_service_out_data", DbTrainLegServiceOutData)


@dataclass
class DbTrainLegCallOutData:
    station: DbTrainLegStationOutData
    platform: Optional[str]
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    service_association_type: Optional[str]
    mileage: Optional[Decimal]


def register_train_leg_call_out_data(conn: Connection) -> None:
    register_type(conn, "train_leg_call_out_data", DbTrainLegCallOutData)


@dataclass
class DbTrainLegStockReportOutData:
    stock_class: Optional[int]
    stock_subclass: Optional[int]
    stock_number: Optional[int]
    stock_cars: Optional[int]


def register_train_leg_stock_report_out_data(conn: Connection) -> None:
    register_type(
        conn, "train_leg_stock_report_out_data", DbTrainLegStockReportOutData
    )


@dataclass
class DbTrainLegStockSegmentOutData:
    stock_start: DbTrainLegStationOutData
    stock_end: DbTrainLegStationOutData
    stock_reports: list[DbTrainLegStockReportOutData]


def register_train_leg_stock_segment_out_data(conn: Connection) -> None:
    register_type(
        conn, "train_leg_stock_segment_out_data", DbTrainLegStockSegmentOutData
    )


@dataclass
class DbTrainLegOutData:
    leg_id: int
    services: list[DbTrainLegServiceOutData]
    calls: list[DbTrainLegCallOutData]
    stock: list[DbTrainLegStockSegmentOutData]


def register_train_leg_out_data(conn: Connection) -> None:
    register_type(conn, "train_leg_out_data", DbTrainLegOutData)


@dataclass
class DbTrainLegCallPointOutData:
    platform: Optional[str]
    latitude: Decimal
    longitude: Decimal


def register_train_leg_call_point_out_data(conn: Connection) -> None:
    register_type(
        conn, "train_leg_call_point_out_data", DbTrainLegCallPointOutData
    )


@dataclass
class DbTrainLegCallPointsOutData:
    station_id: int
    station_crs: str
    station_name: str
    platform: str
    plan_arr: datetime
    act_arr: datetime
    plan_dep: datetime
    act_dep: datetime
    points: list[DbTrainLegCallPointOutData]


def register_train_leg_call_points_out_data(conn: Connection) -> None:
    register_type(
        conn, "train_leg_call_points_out_data", DbTrainLegCallPointsOutData
    )


@dataclass
class DbTrainLegPointsOutData:
    leg_id: int
    operator_id: int
    brand_id: Optional[int]
    call_points: list[DbTrainLegCallPointsOutData]


def register_train_leg_points_out_data(conn: Connection) -> None:
    register_type(conn, "train_leg_points_out_data", DbTrainLegPointsOutData)


@dataclass
class DbTrainLegCallPointPointsOutData(LegLineCall):
    call: DbTrainLegCallPointsOutData
    point: DbTrainLegCallPointOutData

    def get_id(self) -> int:
        return get_node_id_from_crs_and_platform(
            self.call.station_crs, self.point.platform
        )

    def get_call_info_text(
        self, params: MarkerTextParams, values: MarkerTextValues
    ) -> str:
        def get_call_info_time_string(call_time: Optional[datetime]) -> str:
            if call_time is None:
                return "--"
            return f"{call_time.strftime('%H%M')}"

        plan_arr_str = get_call_info_time_string(self.call.plan_arr)
        plan_dep_str = get_call_info_time_string(self.call.plan_dep)
        act_arr_str = get_call_info_time_string(self.call.act_arr)
        act_dep_str = get_call_info_time_string(self.call.act_dep)
        arr_string = f"<b>arr</b> plan {plan_arr_str} act {act_arr_str}"
        dep_string = f"<b>dep</b> plan {plan_dep_str} act {act_dep_str}"
        time_string = f"{arr_string}<br/>{dep_string}"
        return f"<h1>{self.call.station_name} ({self.call.station_crs})</h1>{time_string}"

    def get_call_identifier(self) -> str:
        return self.call.station_crs

    def get_point(self) -> Point:
        return Point(float(self.point.latitude), float(self.point.longitude))

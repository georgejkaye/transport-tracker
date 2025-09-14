from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from psycopg import Connection

from api.classes.train.association import AssociationType
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
    crs: str
    name: str


@dataclass
class DbTrainLegOperatorOutData:
    id: int
    code: str
    name: str
    bg_colour: str
    fg_colour: str


@dataclass
class DbTrainLegServiceOutData:
    service_id: int
    unique_identifier: str
    run_date: datetime
    headcode: str
    start_datetime: datetime
    origins: list[DbTrainLegStationOutData]
    destinations: list[DbTrainLegStationOutData]
    operator: list[DbTrainLegOperatorOutData]
    brand: list[DbTrainLegOperatorOutData]


@dataclass
class DbTrainLegCallOutData:
    station: DbTrainLegStationOutData
    platform: Optional[str]
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    act_dep: Optional[datetime]
    service_association_type: Optional[str]
    mileage: Optional[Decimal]


@dataclass
class DbTrainLegStockReportOutData:
    stock_class: Optional[int]
    stock_subclass: Optional[int]
    stock_number: Optional[int]
    stock_cars: Optional[int]


@dataclass
class DbTrainLegStockSegmentOutData:
    stock_start: DbTrainLegStationOutData
    stock_end: DbTrainLegStationOutData
    stock_reports: DbTrainLegStockReportOutData


@dataclass
class DbTrainLegOutData:
    train_leg_id: int
    services: list[DbTrainLegServiceOutData]
    calls: list[DbTrainLegCallOutData]
    stock: list[DbTrainLegStockSegmentOutData]


def register_train_leg_out_data(conn: Connection) -> None:
    register_type(
        conn, "train_leg_operator_out_data", DbTrainLegOperatorOutData
    )
    register_type(conn, "train_leg_station_out_data", DbTrainLegStationOutData)
    register_type(conn, "train_leg_service_out_data", DbTrainLegServiceOutData)
    register_type(conn, "train_leg_call_out_data", DbTrainLegCallOutData)
    register_type(
        conn, "train_leg_stock_report_out_data", DbTrainLegStockReportOutData
    )
    register_type(
        conn, "train_leg_stock_segment_out_data", DbTrainLegStockSegmentOutData
    )
    register_type(conn, "train_leg_out_data", DbTrainLegOutData)

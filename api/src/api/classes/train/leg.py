from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from api.classes.train.association import AssociationType
from api.classes.train.service import (
    DbTrainAssociatedServiceInData,
    DbTrainCallInData,
    DbTrainServiceEndpointInData,
    DbTrainServiceInData,
    ShortAssociatedService,
    ShortTrainService,
    TrainServiceInData,
    register_short_associated_service_types,
    register_short_train_service_types,
)
from api.classes.train.station import (
    TrainStationIdentifiers,
    get_multiple_short_station_string,
)
from api.classes.train.stock import StockReport
from api.utils.database import register_type
from api.utils.times import get_hourmin_string
from psycopg import Connection


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
    service: TrainServiceInData
    station_crs: str
    station_name: str
    arr_call: Optional[TrainLegCallCallInData]
    dep_call: Optional[TrainLegCallCallInData]
    mileage: Optional[Decimal]
    association_type: Optional[AssociationType]


@dataclass
class TrainStockReportInData:
    stock_report: list[StockReport]
    start_call: TrainLegCallInData
    end_call: TrainLegCallInData
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
    int,
    list[DbTrainServiceInData],
    list[DbTrainServiceEndpointInData],
    list[DbTrainCallInData],
    list[DbTrainAssociatedServiceInData],
    list[DbTrainLegCallInData],
    Optional[Decimal],
    Optional[list[DbTrainStockSegmentInData]],
]


def register_stock_report_types(conn: Connection) -> None:
    register_type(conn, "TrainLegStockOutData", StockReport)


@dataclass
class ShortLegSegment:
    start: TrainStationIdentifiers
    end: TrainStationIdentifiers
    duration: timedelta
    mileage: Optional[Decimal]
    stocks: list[StockReport]


def register_short_leg_segment(
    segment_start: datetime,
    start_station: TrainStationIdentifiers,
    end_station: TrainStationIdentifiers,
    distance: Decimal,
    duration: timedelta,
    stock_data: list[StockReport],
) -> ShortLegSegment:
    return ShortLegSegment(
        start_station,
        end_station,
        duration,
        distance,
        stock_data,
    )


def register_short_leg_segment_types(conn: Connection) -> None:
    register_stock_report_types(conn)
    register_type(conn, "TrainLegStockOutData", ShortLegSegment)


@dataclass
class ShortLegCall:
    station: TrainStationIdentifiers
    platform: Optional[str]
    plan_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_arr: Optional[datetime]
    act_dep: Optional[datetime]
    associated_service: Optional[list[ShortAssociatedService]]
    leg_stock: Optional[list[StockReport]]
    mileage: Optional[Decimal]


def register_short_leg_call_types(conn: Connection) -> None:
    register_stock_report_types(conn)
    register_short_associated_service_types(conn)
    register_type(conn, "TrainLegCallOutData", ShortLegCall)


@dataclass
class ShortLeg:
    id: int
    user_id: int
    leg_start: datetime
    services: dict[str, ShortTrainService]
    calls: list[ShortLegCall]
    stocks: list[ShortLegSegment]
    distance: Optional[Decimal]
    duration: Optional[timedelta]


def register_leg_data_types(conn: Connection) -> None:
    register_short_train_service_types(conn)
    register_short_leg_call_types(conn)
    register_short_leg_segment_types(conn)
    register_type(conn, "TrainLegOutData", ShortLeg)

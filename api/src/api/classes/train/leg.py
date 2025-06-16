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
from api.utils.times import change_timezone, get_hourmin_string
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
    distance: Decimal
    stock_reports: list[TrainStockReportInData]


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
    Decimal,
    list[DbTrainStockSegmentInData],
]


def register_stock_report(
    stock_class: int, stock_subclass: int, stock_number: int, stock_cars: int
) -> StockReport:
    return StockReport(stock_class, stock_subclass, stock_number, stock_cars)


def register_stock_report_types(conn: Connection) -> None:
    register_type(conn, "TrainLegStockOutData", register_stock_report)


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
    register_type(conn, "TrainLegStockOutData", register_short_leg_segment)


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


def register_leg_call_data(
    arr_call_id: int,
    arr_service_id: str,
    arr_service_run_date: datetime,
    plan_arr: datetime,
    act_arr: datetime,
    dep_call_id: int,
    dep_service_id: str,
    dep_service_run_date: datetime,
    plan_dep: datetime,
    act_dep: datetime,
    station: TrainStationIdentifiers,
    platform: str,
    mileage: Decimal,
    stocks: list[StockReport],
    assocs: list[ShortAssociatedService],
) -> ShortLegCall:
    return ShortLegCall(
        station,
        platform,
        change_timezone(plan_arr),
        change_timezone(plan_dep),
        change_timezone(act_arr),
        change_timezone(act_dep),
        assocs,
        stocks,
        mileage,
    )


def register_short_leg_call_types(conn: Connection) -> None:
    register_stock_report_types(conn)
    register_short_associated_service_types(conn)
    register_type(conn, "TrainLegCallOutData", register_leg_call_data)


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


def register_leg_data(
    leg_id: int,
    user_id: int,
    leg_start: datetime,
    leg_services: list[ShortTrainService],
    leg_calls: list[ShortLegCall],
    leg_stocks: list[ShortLegSegment],
    leg_distance: Decimal,
    leg_duration: timedelta,
) -> ShortLeg:
    leg_services_dict: dict[str, ShortTrainService] = {}
    for service in leg_services:
        leg_services_dict[service.service_id] = service
    return ShortLeg(
        leg_id,
        user_id,
        leg_start,
        leg_services_dict,
        leg_calls,
        leg_stocks,
        leg_distance,
        leg_duration,
    )


def register_leg_data_types(conn: Connection) -> None:
    register_short_train_service_types(conn)
    register_short_leg_call_types(conn)
    register_short_leg_segment_types(conn)
    register_type(conn, "TrainLegOutData", register_leg_data)

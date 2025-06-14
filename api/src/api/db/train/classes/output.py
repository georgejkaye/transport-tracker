from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from psycopg import Connection

from api.utils.times import change_timezone
from api.utils.database import register_type
from api.db.train.stations import TrainLegCallStationInData
from api.db.train.toc import OperatorData
from api.db.train.points import PointTimes
from api.classes.train.stock import StockReport
from api.db.train.select.service import (
    ShortAssociatedService,
    ShortTrainService,
    register_short_associated_service_types,
    register_short_train_service_types,
)


def register_stock_report(
    stock_class: int, stock_subclass: int, stock_number: int, stock_cars: int
) -> StockReport:
    return StockReport(stock_class, stock_subclass, stock_number, stock_cars)


def register_stock_report_types(conn: Connection):
    register_type(conn, "TrainLegStockOutData", register_stock_report)


def string_of_enumerated_stock_report(report: tuple[int, StockReport]) -> str:
    _, actual_report = report
    return string_of_stock_report(actual_report)


def string_of_stock_report(report: StockReport) -> str:
    if report.class_no is None:
        return "Unknown"
    if report.stock_no is not None:
        return str(report.stock_no)
    if report.subclass_no is None:
        return f"Class {report.class_no}"
    return f"Class {report.class_no}/{report.subclass_no}"


@dataclass
class ShortLegSegment:
    start: TrainLegCallStationInData
    end: TrainLegCallStationInData
    duration: timedelta
    mileage: Optional[Decimal]
    stocks: list[StockReport]


def register_short_leg_segment(
    segment_start: datetime,
    start_station: TrainLegCallStationInData,
    end_station: TrainLegCallStationInData,
    distance: Decimal,
    duration: timedelta,
    stock_data: list[StockReport],
):
    return ShortLegSegment(
        start_station,
        end_station,
        duration,
        distance,
        stock_data,
    )


def register_short_leg_segment_types(conn: Connection):
    register_stock_report_types(conn)
    register_type(conn, "TrainLegStockOutData", register_short_leg_segment)


@dataclass
class ShortLegCall:
    station: TrainLegCallStationInData
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
    station: TrainLegCallStationInData,
    platform: str,
    mileage: Decimal,
    stocks: list[StockReport],
    assocs: list[ShortAssociatedService],
):
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


def register_short_leg_call_types(conn: Connection):
    register_stock_report_types(conn)
    register_short_associated_service_types(conn)
    register_type(conn, "TrainLegCallOutData", register_leg_call_data)


def short_leg_call_to_point_times(leg_call: ShortLegCall) -> PointTimes:
    return PointTimes(
        leg_call.plan_arr, leg_call.plan_dep, leg_call.act_arr, leg_call.act_dep
    )


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


def register_operator_data(
    operator_id: int,
    operator_code: str,
    operator_name: str,
    operator_bg: str,
    operator_fg: str,
):
    return OperatorData(
        operator_id, operator_code, operator_name, operator_bg, operator_fg
    )


def register_leg_data(
    leg_id: int,
    user_id: int,
    leg_start: datetime,
    leg_services: list[ShortTrainService],
    leg_calls: list[ShortLegCall],
    leg_stocks: list[ShortLegSegment],
    leg_distance: Decimal,
    leg_duration: timedelta,
):
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


def register_leg_data_types(conn: Connection):
    register_short_train_service_types(conn)
    register_short_leg_call_types(conn)
    register_short_leg_segment_types(conn)
    register_type(conn, "TrainLegOutData", register_leg_data)


def get_operator_colour_from_leg(leg: ShortLeg) -> str:
    service_key = list(leg.services.keys())[0]
    service = leg.services[service_key]
    if service.brand is not None and service.brand.bg is not None:
        return service.brand.bg
    if service.operator.bg is None:
        return "#000000"
    return service.operator.bg

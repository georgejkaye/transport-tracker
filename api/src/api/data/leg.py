from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable, Optional
from api.user import User
from psycopg import Connection

from api.utils.database import register_type
from api.utils.times import change_timezone
from api.data.toc import OperatorData
from api.data.points import PointTimes
from api.data.services import (
    LegCall,
    ShortAssociatedService,
    ShortTrainService,
    TrainServiceRaw,
    insert_services,
    register_short_associated_service_types,
    register_short_train_service_types,
    string_of_associated_type,
)
from api.data.stations import ShortTrainStation
from api.data.stock import Formation


@dataclass
class StockReport:
    class_no: Optional[int]
    subclass_no: Optional[int]
    stock_no: Optional[int]
    cars: Optional[Formation]


def register_stock_report(
    stock_class: int, stock_subclass: int, stock_number: int, stock_cars: int
):
    return StockReport(
        stock_class, stock_subclass, stock_number, Formation(stock_cars)
    )


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
class LegSegmentStock:
    stock: list[StockReport]
    calls: list[LegCall]
    mileage: Optional[Decimal]


@dataclass
class ShortLegSegment:
    start: ShortTrainStation
    end: ShortTrainStation
    duration: timedelta
    mileage: Optional[Decimal]
    stocks: list[StockReport]


def register_short_leg_segment(
    segment_start: datetime,
    start_station: ShortTrainStation,
    end_station: ShortTrainStation,
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
class Leg:
    service: TrainServiceRaw
    calls: list[LegCall]
    distance: Decimal
    stock: list[LegSegmentStock]


def get_value_or_none[T, U](
    get: Callable[[T], U | None], obj: T | None
) -> U | None:
    if obj is None:
        return None
    return get(obj)


def apply_to_optional[T, U](
    t: Optional[T], fn: Callable[[T], U]
) -> Optional[U]:
    if t is None:
        return None
    return fn(t)


def insert_leg(conn: Connection, user: User, leg: Leg):
    services = [leg.service]
    for assoc in leg.service.divides + leg.service.joins:
        services.append(assoc.service)
    insert_services(conn, services)
    leg_values = leg.distance
    call_values = []
    for call in leg.calls:
        arr_call = call.arr_call
        dep_call = call.dep_call
        if call.change_type:
            assoc_change_type = string_of_associated_type(call.change_type)
        else:
            assoc_change_type = None
        call_values.append(
            (
                apply_to_optional(arr_call, lambda c: c.service_id),
                apply_to_optional(arr_call, lambda c: c.run_date),
                apply_to_optional(arr_call, lambda c: c.station.crs),
                apply_to_optional(arr_call, lambda c: c.plan_arr),
                apply_to_optional(arr_call, lambda c: c.plan_dep),
                apply_to_optional(arr_call, lambda c: c.act_arr),
                apply_to_optional(arr_call, lambda c: c.act_dep),
                apply_to_optional(dep_call, lambda c: c.service_id),
                apply_to_optional(dep_call, lambda c: c.run_date),
                apply_to_optional(dep_call, lambda c: c.station.crs),
                apply_to_optional(dep_call, lambda c: c.plan_arr),
                apply_to_optional(dep_call, lambda c: c.plan_dep),
                apply_to_optional(dep_call, lambda c: c.act_arr),
                apply_to_optional(dep_call, lambda c: c.act_dep),
                call.mileage,
                assoc_change_type,
            )
        )
    stockreport_values = []
    for formation in leg.stock:
        stocks = formation.stock
        for stock in stocks:
            if stock.cars is None:
                stock_cars = None
            else:
                stock_cars = stock.cars.cars
            start_call = formation.calls[0].dep_call
            end_call = formation.calls[-1].arr_call
            stockreport_values.append(
                (
                    apply_to_optional(start_call, lambda c: c.service_id),
                    apply_to_optional(start_call, lambda c: c.run_date),
                    apply_to_optional(start_call, lambda c: c.station.crs),
                    apply_to_optional(start_call, lambda c: c.plan_arr),
                    apply_to_optional(start_call, lambda c: c.plan_dep),
                    apply_to_optional(start_call, lambda c: c.act_arr),
                    apply_to_optional(start_call, lambda c: c.act_dep),
                    apply_to_optional(end_call, lambda c: c.service_id),
                    apply_to_optional(end_call, lambda c: c.run_date),
                    apply_to_optional(end_call, lambda c: c.station.crs),
                    apply_to_optional(end_call, lambda c: c.plan_arr),
                    apply_to_optional(end_call, lambda c: c.plan_dep),
                    apply_to_optional(end_call, lambda c: c.act_arr),
                    apply_to_optional(end_call, lambda c: c.act_dep),
                    stock.class_no,
                    stock.subclass_no,
                    stock.stock_no,
                    stock_cars,
                )
            )
    conn.execute(
        """
        SELECT * FROM InsertLeg(
            %s::integer,
            %s::decimal,
            %s::legcall_data[],
            %s::stockreport_data[]
        )
        """,
        [user.user_id, leg_values, call_values, stockreport_values],
    )
    conn.commit()


@dataclass
class ShortLegCall:
    station: ShortTrainStation
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
    station: ShortTrainStation,
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
    leg_services_dict = {}
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


def select_legs(
    conn: Connection,
    user_id: int,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
    search_leg_id: Optional[int] = None,
) -> list[ShortLeg]:
    register_leg_data_types(conn)
    rows = conn.execute(
        "SELECT SelectLegs(%s, %s, %s, %s)",
        [user_id, search_start, search_end, search_leg_id],
    ).fetchall()

    return [row[0] for row in rows]


def get_operator_colour_from_leg(leg: ShortLeg) -> str:
    service_key = list(leg.services.keys())[0]
    service = leg.services[service_key]
    if service.brand is not None and service.brand.bg is not None:
        return service.brand.bg
    if service.operator.bg is None:
        return "#000000"
    return service.operator.bg

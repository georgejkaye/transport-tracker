from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from psycopg import Connection

from api.utils.database import register_type
from api.utils.times import change_timezone, make_timezone_aware
from api.data.train.retrieve.insert import (
    StockReport,
    TrainLegCallCallInData,
    TrainLegCallInData,
    TrainServiceInData,
)
from api.data.train.retrieve.json import get_service_from_id
from api.data.train.toc import OperatorData
from api.data.train.points import PointTimes
from api.data.train.services import (
    AssociationType,
    ShortAssociatedService,
    ShortTrainService,
    register_short_associated_service_types,
    register_short_train_service_types,
)
from api.data.train.stations import (
    TrainLegCallStationInData,
)


def register_stock_report(
    stock_class: int, stock_subclass: int, stock_number: int, stock_cars: int
):
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


def get_leg_calls_between_calls(
    service: TrainServiceInData,
    start_station_crs: str,
    start_dep_time: datetime,
    end_station_crs: str,
    mileage_offset: Optional[Decimal] = None,
) -> Optional[list[TrainLegCallInData]]:
    start_dep_time = make_timezone_aware(start_dep_time)
    leg_calls = []
    boarded = False
    mileage_offset = Decimal(0)
    for call in service.calls:
        mileage_offset = (
            (mileage_offset + call.mileage)
            if mileage_offset is not None and call.mileage is not None
            else None
        )
        if (
            not boarded
            and call.station_crs == start_station_crs
            and call.plan_dep == start_dep_time
        ):
            boarded = True
        if boarded:
            arr_call = TrainLegCallCallInData(
                service.unique_identifier,
                service.run_date,
                call.plan_arr,
                call.act_arr,
                call.plan_dep,
                call.act_dep,
            )
        else:
            arr_call = None
        for call_association in call.associated_services:
            if call_association.association not in [
                AssociationType.OTHER_DIVIDES,
                AssociationType.THIS_JOINS,
            ]:
                continue
            associated_service = call_association.associated_service
            if associated_service.calls[0].plan_dep is None:
                continue
            associated_leg_calls = get_leg_calls_between_calls(
                associated_service,
                associated_service.calls[0].station_crs,
                associated_service.calls[0].plan_dep,
                end_station_crs,
                mileage_offset,
            )
            if associated_leg_calls is None:
                continue
            if boarded:
                associated_leg_calls[0].arr_call = arr_call
                associated_leg_calls[0].association_type = (
                    call_association.association
                )
            leg_calls.extend(associated_leg_calls)
            return leg_calls
        if boarded:
            leg_call = TrainLegCallInData(
                call.station_crs,
                call.station_name,
                arr_call,
                arr_call,
                (
                    call.mileage - mileage_offset
                    if call.mileage is not None and mileage_offset is not None
                    else None
                ),
                None,
            )
            leg_calls.append(leg_call)
            if call.station_crs == end_station_crs:
                return leg_calls
    return None

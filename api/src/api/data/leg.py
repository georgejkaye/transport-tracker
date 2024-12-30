from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable, Optional
from psycopg import Connection, Cursor

from api.data.toperator import BrandData, OperatorData

from api.data.database import (
    connect,
    optional_to_decimal,
    str_or_null_to_datetime,
)
from api.data.services import (
    Call,
    LegCall,
    ShortAssociatedService,
    ShortCall,
    ShortTrainService,
    TrainServiceRaw,
    insert_services,
    string_of_associated_type,
)
from api.data.stations import ShortTrainStation
from api.data.stock import Formation
from api.times import timezone


@dataclass
class StockReport:
    class_no: Optional[int]
    subclass_no: Optional[int]
    stock_no: Optional[int]
    cars: Optional[Formation]


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
    mileage: Optional[Decimal]
    stocks: list[StockReport]


@dataclass
class Leg:
    service: TrainServiceRaw
    calls: list[LegCall]
    distance: Decimal
    stock: list[LegSegmentStock]


def get_value_or_none[
    T, U
](get: Callable[[T], U | None], obj: T | None) -> U | None:
    if obj is None:
        return None
    return get(obj)


def get_call_from_leg_call_procedure(
    service_id: str,
    run_date: datetime,
    station_crs: str,
    plan_arr: Optional[datetime],
    plan_dep: Optional[datetime],
    act_arr: Optional[datetime],
    act_dep: Optional[datetime],
) -> Optional[str]:
    return f"SELECT getCallFromLegCall({service_id}, {run_date}, {station_crs}, {plan_arr}, {plan_dep}, {act_arr}, {act_dep})"


def select_call_id_from_leg_call(call: Optional[Call]) -> Optional[str]:
    if call is None:
        return None
    return get_call_from_leg_call_procedure(
        call.service_id,
        call.run_date,
        call.station.crs,
        call.plan_arr,
        call.plan_dep,
        call.act_arr,
        call.act_dep,
    )


def call_to_leg_call_data(call: Optional[Call]):
    if call is None:
        return None
    return (
        call.service_id,
        call.run_date,
        call.station.crs,
        call.plan_arr,
        call.plan_dep,
        call.act_arr,
        call.act_dep,
    )


def apply_to_optional[
    T, U
](t: Optional[T], fn: Callable[[T], U]) -> Optional[U]:
    if t is None:
        return None
    return fn(t)


def insert_leg(conn: Connection, cur: Cursor, leg: Leg):
    services = [leg.service]
    for assoc in leg.service.divides + leg.service.joins:
        services.append(assoc.service)
    insert_services(conn, cur, services)
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
    cur.execute(
        """
        SELECT * FROM InsertLeg(
            %s::decimal,
            %s::legcall_data[],
            %s::stockreport_data[]
        )
        """,
        [leg_values, call_values, stockreport_values],
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
    associated_service: Optional[ShortAssociatedService]
    leg_stock: Optional[list[StockReport]]
    mileage: Optional[Decimal]


@dataclass
class ShortLeg:
    id: int
    leg_start: datetime
    services: dict[str, ShortTrainService]
    calls: list[ShortLegCall]
    stocks: list[ShortLegSegment]
    distance: Optional[Decimal]
    duration: Optional[timedelta]


def select_legs(
    cur: Cursor,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
    search_leg_id: Optional[int] = None,
) -> list[ShortLeg]:
    cur.execute("SELECT * FROM SelectLegs(%s, %s)", [search_start, search_end])
    rows = cur.fetchall()
    legs = []
    for row in rows:
        leg_id, leg_start, services, calls, stocks, distance, duration = row
        leg_start_time = datetime.fromisoformat(leg_start).astimezone(timezone)
        services_dict = {}
        for service in services:
            service = service[0]
            service_id: str = service["service_id"]
            service_run_date = datetime.fromisoformat(service["run_date"])
            service_headcode: str = service["headcode"]
            service_start = datetime.fromisoformat(service["service_start"])
            service_operator_id: int = service["operator_id"]
            service_operator_code: str = service["operator_code"]
            service_operator_name: str = service["operator_name"]
            service_operator_bg: str = service["operator_bg"]
            service_operator_fg: str = service["operator_fg"]
            service_brand_id: int = service["brand_id"]
            service_brand_code: str = service["brand_code"]
            service_brand_name: str = service["brand_name"]
            service_brand_bg: str = service["brand_bg"]
            service_brand_fg: str = service["brand_fg"]
            service_power: str = service["power"]
            service_origins = []
            for origin in service["origins"]:
                station_name = origin["station_name"]
                station_crs = origin["station_crs"]
                service_origin = ShortTrainStation(station_name, station_crs)
                service_origins.append(service_origin)
            service_destinations = []
            for destination in service["destinations"]:
                station_name = destination["station_name"]
                station_crs = destination["station_crs"]
                service_destination = ShortTrainStation(
                    station_name, station_crs
                )
                service_destinations.append(service_destination)
            service_calls: list[ShortCall] = []
            service_assocs: list[ShortAssociatedService] = []
            for call in service["calls"]:
                call_station = ShortTrainStation(
                    call["station_name"], call["station_crs"]
                )
                call_platform: str = call["platform"]
                if call.get("plan_arr"):
                    call_plan_arr = datetime.fromisoformat(
                        call["plan_arr"]
                    ).astimezone(timezone)
                else:
                    call_plan_arr = None
                if call.get("plan_dep"):
                    call_plan_dep = datetime.fromisoformat(
                        call["plan_dep"]
                    ).astimezone(timezone)
                else:
                    call_plan_dep = None
                if call.get("act_arr"):
                    call_act_arr = datetime.fromisoformat(
                        call["act_arr"]
                    ).astimezone(timezone)
                else:
                    call_act_arr = None
                if call.get("act_dep"):
                    call_act_dep = datetime.fromisoformat(
                        call["act_dep"]
                    ).astimezone(timezone)
                else:
                    call_act_dep = None
                call_assocs: list[ShortAssociatedService] = []
                if call.get("associations"):
                    for association in call["associations"]:
                        associated_type = association["associated_type"]
                        associated_service = ShortAssociatedService(
                            association["associated_id"],
                            datetime.fromisoformat(
                                association["associated_run_date"]
                            ),
                            associated_type,
                        )
                        call_assocs.append(associated_service)
                        service_assocs.append(associated_service)
                call_mileage = optional_to_decimal(call["mileage"])
                service_call = ShortCall(
                    call_station,
                    call_platform,
                    call_plan_arr,
                    call_plan_dep,
                    call_act_arr,
                    call_act_dep,
                    call_assocs,
                    call_mileage,
                )
                service_calls.append(service_call)
            service_operator = OperatorData(
                service_operator_id,
                service_operator_code,
                service_operator_name,
                service_operator_bg,
                service_operator_fg,
            )
            if service_brand_id is None:
                service_brand = None
            else:
                service_brand = BrandData(
                    service_brand_id,
                    service_brand_code,
                    service_brand_name,
                    service_brand_bg,
                    service_brand_fg,
                )
            service_object = ShortTrainService(
                service_id,
                service_headcode,
                service_run_date,
                service_start,
                service_origins,
                service_destinations,
                service_operator,
                service_brand,
                service_power,
                service_calls,
                service_assocs,
            )
            services_dict[service_id] = service_object
        leg_calls = []
        for call in calls:
            leg_call_station = ShortTrainStation(
                call["station_name"], call["station_crs"]
            )
            leg_call_platform: str = call["platform"]
            leg_call_plan_arr = str_or_null_to_datetime(
                call.get("plan_arr"), timezone
            )
            leg_call_plan_dep = str_or_null_to_datetime(
                call.get("plan_dep"), timezone
            )
            leg_call_act_arr = str_or_null_to_datetime(
                call.get("act_arr"), timezone
            )
            leg_call_act_dep = str_or_null_to_datetime(
                call.get("act_dep"), timezone
            )
            leg_call_mileage = optional_to_decimal(call.get("mileage"))
            if call.get("associations"):
                assoc = call["associations"][0]
                assoc_id = assoc["associated_id"]
                assoc_run_date = datetime.fromisoformat(
                    assoc["associated_run_date"]
                )
                assoc_type = assoc["associated_type"]
                leg_call_assoc = ShortAssociatedService(
                    assoc_id, assoc_run_date, assoc_type
                )
            else:
                leg_call_assoc = None
            leg_call_stock: Optional[list[StockReport]] = None
            if call.get("new_stock"):
                leg_call_stock = []
                for new_stock in call["new_stock"]:
                    stock_class = new_stock.get("stock_class")
                    stock_subclass = new_stock.get("stock_subclass")
                    stock_number = new_stock.get("stock_number")
                    stock_cars = new_stock.get("stock_cars")
                    if stock_cars is None:
                        stock_formation = None
                    else:
                        stock_formation = Formation(stock_cars)
                    stock_obj = StockReport(
                        stock_class,
                        stock_subclass,
                        stock_number,
                        stock_formation,
                    )
                    leg_call_stock.append(stock_obj)
            leg_call = ShortLegCall(
                leg_call_station,
                leg_call_platform,
                leg_call_plan_arr,
                leg_call_plan_dep,
                leg_call_act_arr,
                leg_call_act_dep,
                leg_call_assoc,
                leg_call_stock,
                leg_call_mileage,
            )
            leg_calls.append(leg_call)
        leg_stock = []
        for segment in stocks:
            segment_start_crs: str = segment["start_crs"]
            segment_start_name: str = segment["start_name"]
            segment_start = ShortTrainStation(
                segment_start_name, segment_start_crs
            )
            segment_end_crs: str = segment["end_crs"]
            segment_end_name: str = segment["end_name"]
            segment_end = ShortTrainStation(segment_end_name, segment_end_crs)
            segment_distance = optional_to_decimal(segment["distance"])
            segment_stocks: list[StockReport] = []
            for stock in segment["stocks"][0]["stocks"]:
                stock_class: Optional[int] = stock.get("stock_class")
                stock_subclass: Optional[int] = stock.get("stock_subclass")
                stock_number: Optional[int] = stock.get("stock_number")
                stock_cars: Optional[int] = stock.get("stock_cars")
                if stock_cars is None:
                    stock_formation = None
                else:
                    stock_formation = Formation(stock_cars)
                stock_report = StockReport(
                    stock_class, stock_subclass, stock_number, stock_formation
                )
                segment_stocks.append(stock_report)
            segment = ShortLegSegment(
                segment_start,
                segment_end,
                segment_distance,
                segment_stocks,
            )
            leg_stock.append(segment)
        leg_object = ShortLeg(
            leg_id,
            leg_start_time,
            services_dict,
            leg_calls,
            leg_stock,
            Decimal(distance),
            duration,
        )
        legs.append(leg_object)
    return legs


if __name__ == "__main__":
    with connect() as (conn, cur):
        select_legs(cur, None, None)

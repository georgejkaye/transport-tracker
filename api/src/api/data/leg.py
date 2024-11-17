from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable, Optional
from api.data.toperator import BrandData, OperatorData
from psycopg2._psycopg import connection, cursor

from api.data.database import (
    NoEscape,
    connect,
    insert,
    int_or_none_to_str_or_none,
    number_or_none_to_str,
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


def get_service_fields(service: TrainServiceRaw) -> list[str | None]:
    return [
        str(service.id),
        service.run_date.isoformat(),
        service.headcode,
        service.operator_id,
        service.brand_id,
    ]


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


def insert_leg(conn: connection, cur: cursor, leg: Leg):
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


def get_endpoint_statement(origin: bool, column_name: str) -> str:
    return f"""
        WITH endpoint_info AS (
            SELECT service_id, run_date, Station.station_name, Station.station_crs
            FROM ServiceEndpoint
            INNER JOIN Station
            ON ServiceEndpoint.station_crs = Station.station_crs
            WHERE origin = {origin}
        )
        SELECT
            endpoint_info.service_id, endpoint_info.run_date,
            JSON_AGG(endpoint_info.*) AS {column_name}
        FROM endpoint_info
        GROUP BY (endpoint_info.service_id, endpoint_info.run_date)
    """


def get_associations_statement(call_table: str) -> str:
    return f"""
    LEFT JOIN (
        WITH AssociationInfo AS (
            SELECT
                call_id, associated_id,
                associated_run_date, associated_type
            FROM AssociatedService
        )
        SELECT
            call_id,
            JSON_AGG(AssociationInfo.*) AS associations
        FROM AssociationInfo
        GROUP BY call_id
    ) Association
    ON {call_table}.call_id = Association.call_id
    """


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
    cur: cursor,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
    search_leg_id: Optional[int] = None,
) -> list[ShortLeg]:
    statement = f"""
        SELECT
            Leg.leg_id,
            COALESCE(
                legcalls -> 0 ->> 'plan_dep',
                legcalls -> 0 ->> 'act_dep',
                legcalls -> 0 ->> 'plan_arr',
                legcalls-> 0 ->> 'act_arr'
            ) AS leg_start,
            services, legcalls, stocks, Leg.distance,
            COALESCE(legcalls -> -1 ->> 'act_arr', legcalls -> -1 ->> 'plan_arr')::TIMESTAMP
            -
            COALESCE(legcalls -> 0 ->> 'act_dep', legcalls -> 0 ->> 'plan_dep')::TIMESTAMP
            AS duration
        FROM Leg
        INNER JOIN (
            WITH legcall_info AS (
                SELECT
                    leg_id, LegCall.arr_call_id,
                    ArrCall.service_id AS arr_id, ArrCall.run_date AS arr_run_date,
                    ArrCall.plan_arr, ArrCall.act_arr,
                    LegCall.dep_call_id,
                    DepCall.service_id AS dep_id, DepCall.run_date AS dep_run_date,
                    DepCall.plan_dep, DepCall.act_dep,
                    COALESCE(ArrCall.station_crs, DepCall.station_crs) AS station_crs,
                    COALESCE(ArrStation.station_name, DepStation.station_name) AS station_name,
                    COALESCE(ArrCall.platform, DepCall.platform) AS platform,
                    LegCall.mileage, associations, new_stock
                FROM LegCall
                LEFT JOIN Call ArrCall
                ON LegCall.arr_call_id = ArrCall.call_id
                LEFT JOIN Station ArrStation
                ON ArrCall.station_crs = ArrStation.station_crs
                LEFT JOIN Call DepCall
                ON LegCall.dep_call_id = DepCall.call_id
                LEFT JOIN Station DepStation
                ON DepCall.station_crs = DepStation.station_crs
                LEFT JOIN (
                    WITH StockInfo AS (
                        SELECT start_call, stock_class, stock_subclass,
                            stock_number, stock_cars
                        FROM StockSegment
                        INNER JOIN StockSegmentReport
                        ON StockSegment.stock_segment_id = StockSegmentReport.stock_segment_id
                        INNER JOIN StockReport
                        ON StockSegmentReport.stock_report_id = StockReport.stock_report_id
                        INNER JOIN Call
                        ON start_call = call_id
                    )
                    SELECT start_call, JSON_AGG(StockInfo.*) AS new_stock
                    FROM StockInfo
                    GROUP BY start_call
                ) StockDetails
                ON LegCall.dep_call_id = StockDetails.start_call
                { get_associations_statement("ArrCall") }
                ORDER BY COALESCE(ArrCall.plan_arr, ArrCall.act_arr, DepCall.plan_dep, DepCall.act_arr) ASC
            )
            SELECT leg_id, JSON_AGG(legcall_info.* ORDER BY COALESCE(plan_arr, act_arr, plan_dep, act_dep) ASC) as legcalls
            FROM legcall_info
            GROUP BY leg_id
        ) legcall_table
        ON legcall_table.leg_id = leg.leg_id
        INNER JOIN (
            SELECT
                LegService.leg_id,
                JSON_AGG(service_details ORDER BY service_start ASC) AS services
            FROM (
                SELECT DISTINCT leg.leg_id, service.service_id
                FROM Leg
                INNER JOIN Legcall
                ON leg.leg_id = legcall.leg_id
                INNER JOIN call
                ON (
                    Call.call_id = LegCall.arr_call_id
                    OR Call.call_id = LegCall.dep_call_id
                )
                INNER JOIN service
                ON call.service_id = service.service_id
                AND call.run_date = service.run_date
            ) LegService
            INNER JOIN (
                WITH service_info AS (
                    SELECT
                        Service.service_id, Service.run_date, headcode, origins,
                        destinations, calls, Operator.operator_id,
                        Operator.operator_code, Operator.operator_name,
                        Operator.bg_colour AS operator_bg,
                        Operator.fg_colour AS operator_fg, Brand.brand_id,
                        Brand.brand_code, Brand.brand_name,
                        Brand.bg_colour AS brand_bg, Brand.fg_colour AS brand_fg,
                        power,
                        COALESCE(calls -> 0 ->> 'plan_arr', calls -> 0 ->> 'act_arr', calls -> 0 ->> 'plan_dep', calls -> 0 ->> 'act_dep') AS service_start
                    FROM Service
                    INNER JOIN (
                        {get_endpoint_statement(True, "origins")}
                    ) origin_details
                    On origin_details.service_id = Service.service_id
                    AND origin_details.run_date = Service.run_date
                    INNER JOIN (
                        {get_endpoint_statement(False, "destinations")}
                    ) destination_details
                    On destination_details.service_id = Service.service_id
                    AND destination_details.run_date = Service.run_date
                    INNER JOIN (
                        WITH call_info AS (
                            SELECT
                                Call.call_id, service_id, run_date, station_name, Call.station_crs,
                                platform, plan_arr, plan_dep, act_arr, act_dep,
                                mileage, associations
                            FROM Call
                            INNER JOIN Station
                            ON Call.station_crs = Station.station_crs
                            {get_associations_statement("Call")}
                            ORDER BY COALESCE(plan_arr, act_arr, plan_dep, act_dep) ASC
                        )
                        SELECT service_id, run_date, JSON_AGG(call_info.*) AS calls
                        FROM call_info
                        GROUP BY (service_id, run_date)
                    ) call_details
                    ON Service.service_id = call_details.service_id
                    INNER JOIN Operator
                    ON Service.operator_id = Operator.operator_id
                    LEFT JOIN Brand
                    ON Service.brand_id = Brand.brand_id
                    ORDER BY service_start ASC
                )
                SELECT
                    service_id, run_date, service_start,
                    JSON_AGG(service_info.*) AS service_details
                FROM service_info
                GROUP BY (service_id, run_date, service_start)
                ORDER BY service_start ASC
            ) ServiceDetails
            ON ServiceDetails.service_id = LegService.service_id
            GROUP BY LegService.leg_id
        ) LegServices
        ON LegServices.leg_id = Leg.leg_id
        INNER JOIN (
            WITH StockSegment AS (
                WITH StockSegmentDetail AS (
                    WITH StockDetail AS (
                        SELECT
                            stock_class, stock_subclass, stock_number,
                            stock_cars, start_call, end_call
                        FROM StockReport
                        INNER JOIN StockSegmentReport
                        ON StockReport.stock_report_id = StockSegmentReport.stock_report_id
                        INNER JOIN StockSegment
                        ON StockSegmentReport.stock_segment_id = StockSegment.stock_segment_id
                    )
                    SELECT
                        start_call, end_call, JSON_AGG(StockDetail.*) AS stocks
                    FROM StockDetail
                    GROUP BY start_call, end_call
                )
                SELECT
                    StartLegCall.leg_id,
                    COALESCE(StartCall.plan_dep, StartCall.plan_arr, StartCall.act_dep, StartCall.act_arr) AS segment_start,
                    StartStation.station_crs AS start_crs,
                    StartStation.station_name AS start_name,
                    EndStation.station_crs AS end_crs,
                    EndStation.station_name AS end_name,
                    Service.service_id, Service.run_date,
                    EndLegCall.mileage - StartLegCall.mileage AS distance,
                    COALESCE(EndCall.act_arr, EndCall.plan_arr) -
                    COALESCE(StartCall.act_dep, StartCall.plan_dep) AS duration,
                    JSON_AGG(StockSegmentDetail.*) AS stocks
                FROM StockSegmentDetail
                INNER JOIN Call StartCall
                ON StockSegmentDetail.start_call = StartCall.call_id
                INNER JOIN Station StartStation
                ON StartCall.station_crs = StartStation.station_crs
                INNER JOIN Call EndCall
                ON StockSegmentDetail.end_call = EndCall.call_id
                INNER JOIN Station EndStation
                ON EndCall.station_crs = EndStation.station_crs
                INNER JOIN LegCall StartLegCall
                ON StartLegCall.dep_call_id = StartCall.call_id
                INNER JOIN LegCall EndLegCall
                ON EndLegCall.arr_call_id = EndCall.call_id
                INNER JOIN Service
                ON StartCall.service_id = Service.service_id
                AND StartCall.run_date = Service.run_date
                GROUP BY
                    StartLegCall.leg_id, segment_start, start_crs, start_name,
                    end_crs, end_name, Service.service_id, Service.run_date,
                    distance, duration
            )
            SELECT leg_id, JSON_AGG(StockSegment.* ORDER BY segment_start ASC) AS stocks
            FROM StockSegment
            GROUP BY leg_id
        ) StockDetails
        ON StockDetails.leg_id = Leg.leg_id
    """
    wheres = []
    if search_start is not None:
        wheres.append("leg_start >= %(start)s")
    if search_end is not None:
        wheres.append("leg_start < %(end)s")
    if search_leg_id is not None:
        wheres.append("Leg.leg_id = %(leg)s")
    if len(wheres) != 0:
        where_string = f"\nWHERE {" AND ".join(wheres)}"
    else:
        where_string = ""
    order_string = "ORDER BY leg_start DESC"
    full_statement = f"{statement}\n{where_string}\n{order_string}"
    cur.execute(
        full_statement,
        {"start": search_start, "end": search_end, "leg": search_leg_id},
    )
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
    conn, cur = connect()
    select_legs(cur, None, None)

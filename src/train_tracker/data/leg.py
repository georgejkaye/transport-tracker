from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from re import L, search
from typing import Callable, Optional
from psycopg2._psycopg import connection, cursor

from train_tracker.data.core import get_or_throw
from train_tracker.data.database import (
    NoEscape,
    connect,
    datetime_or_none_to_raw_str,
    datetime_or_none_to_str,
    insert,
    int_or_none_to_str_or_none,
    number_or_none_to_str,
    str_or_none_to_str,
    str_or_null_to_datetime,
)
from train_tracker.data.services import (
    AssociatedService,
    AssociatedType,
    Call,
    LegCall,
    ShortAssociatedService,
    ShortCall,
    ShortTrainService,
    TrainService,
    get_calls_between_stations,
    insert_services,
    string_of_associated_type,
    string_to_associated_type,
)
from train_tracker.data.stations import ShortTrainStation
from train_tracker.data.stock import Formation, Stock


@dataclass
class StockReport:
    class_no: Optional[int]
    subclass_no: Optional[int]
    stock_no: Optional[int]
    cars: Optional[Formation]

def string_of_enumerated_stock_report(report : tuple[int, StockReport]) -> str:
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
class ShortLegSegmentStock:
    stock: list[StockReport]
    start_station: ShortTrainStation
    end_station: ShortTrainStation
    mileage: Optional[Decimal]


@dataclass
class Leg:
    service: TrainService
    calls: list[LegCall]
    distance: Decimal
    stock: list[LegSegmentStock]


def get_value_or_none[T, U](get: Callable[[T], U | None], obj: T | None) -> U | None:
    if obj is None:
        return None
    return get(obj)


def get_service_fields(service: TrainService) -> list[str | None]:
    return [
        str(service.id),
        service.run_date.isoformat(),
        service.headcode,
        service.operator_id,
        service.brand_id,
    ]


def select_call_id_from_leg_call(call: Optional[Call], arr : bool) -> Optional[NoEscape]:
    if call is None:
        return None
    if arr:
        field_stub = "arr"
        plan = call.plan_arr
    else:
        field_stub = "dep"
        plan = call.plan_dep
    column = f"plan_{field_stub}"
    if plan is None:
        condition = f"{column} IS NULL"
    else:
        condition = f"{column} = '{plan.isoformat()}'"
    select_call_id_statement = f"""(
        SELECT call_id FROM Call
        WHERE service_id = '{call.service_id}'
        AND run_date = '{call.run_date.isoformat()}'
        AND station_crs = '{call.station.crs}'
        AND {condition}
    )"""
    return NoEscape(select_call_id_statement)


def insert_leg(conn: connection, cur: cursor, leg: Leg):
    services = [leg.service]
    for assoc in leg.service.divides + leg.service.joins:
        services.append(assoc.service)
    insert_services(conn, cur, services)

    leg_statement = """
        INSERT INTO Leg(distance) VALUES (%(distance)s) RETURNING leg_id
    """
    cur.execute(leg_statement, {"distance": leg.distance})
    leg_id: int = cur.fetchall()[0][0]
    call_fields = ["leg_id", "arr_call_id", "dep_call_id", "mileage", "assoc_type"]
    call_values = []
    for call in leg.calls:
        arr_call = call.arr_call
        dep_call = call.dep_call
        if call.change_type:
            assoc_change_type = string_of_associated_type(call.change_type)
        else:
            assoc_change_type = None
        call_values.append(
            [
                str(leg_id),
                select_call_id_from_leg_call(arr_call, True),
                select_call_id_from_leg_call(dep_call, False),
                number_or_none_to_str(call.mileage),
                assoc_change_type
            ]
        )
    insert(cur, "LegCall", call_fields, call_values)
    legstock_fields = [
        "start_call",
        "end_call",
        "distance",
    ]
    stockreport_fields = [
        "start_call",
        "end_call",
        "stock_class",
        "stock_subclass",
        "stock_number",
        "stock_cars",
    ]
    legstock_values = []
    stockreport_values = []
    for formation in leg.stock:
        stocks = formation.stock
        start_call = select_call_id_from_leg_call(formation.calls[0].dep_call, False)
        end_call = select_call_id_from_leg_call(formation.calls[-1].arr_call, True)
        legstock_values.append([
            start_call,
            end_call,
            number_or_none_to_str(formation.mileage)
        ])
        for stock in stocks:
            stock_class = int_or_none_to_str_or_none(stock.class_no)
            stock_subclass = int_or_none_to_str_or_none(stock.subclass_no)
            if stock.cars is None:
                stock_cars = None
            else:
                stock_cars = str(stock.cars.cars)
            stock_number = int_or_none_to_str_or_none(stock.stock_no)
            stockreport_values.append(
                [
                    start_call,
                    end_call,
                    stock_class,
                    stock_subclass,
                    stock_number,
                    stock_cars,
                ]
            )
    insert(cur, "StockSegment", legstock_fields, legstock_values)
    insert(cur, "StockReport", stockreport_fields, stockreport_values)
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
    leg_start: datetime
    services : dict[str, ShortTrainService]
    calls: list[ShortLegCall]
    stocks: list[ShortLegSegmentStock]
    distance: Decimal

def select_legs(
    cur: cursor, search_start: Optional[datetime] = None, search_end: Optional[datetime] = None
) -> list[ShortLeg]:
    statement = f"""
        SELECT
            Leg.leg_id, (legcalls -> 0 ->> 'plan_dep') AS leg_start,
            services, legcalls, stocks, distance
        FROM Leg
        INNER JOIN (
            WITH legcall_info AS (
                SELECT
                    leg_id, LegCall.arr_call_id,
                    ArrCall.service_id AS arr_id, ArrCall.run_date AS arr_run_date,
                    ArrCall.plan_arr,
                    LegCall.dep_call_id,
                    DepCall.service_id AS dep_id, DepCall.run_date AS dep_run_date,
                    DepCall.plan_dep,
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
                    )
                    SELECT start_call, JSON_AGG(StockInfo.*) AS new_stock
                    FROM StockInfo
                    GROUP BY start_call
                ) StockDetails
                ON LegCall.dep_call_id = StockDetails.start_call
                { get_associations_statement("ArrCall") }
                ORDER BY COALESCE(ArrCall.plan_arr, DepCall.plan_dep) ASC
            )
            SELECT leg_id, JSON_AGG(legcall_info.*) as legcalls
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
                        destinations, calls, Service.operator_id, operator_name,
                        Service.brand_id, brand_name, power,
                        COALESCE(calls -> 0 ->> 'plan_arr', calls -> 0 ->> 'plan_dep') AS service_start
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
                            ORDER BY COALESCE(plan_arr, plan_dep) ASC
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
            WITH StockSegments AS (
                WITH StockDetails AS (
                    SELECT
                        Leg.leg_id, stock_class, stock_subclass, stock_number,
                        stock_cars, stocksegment.distance,
                        StartStation.station_crs AS start_crs,
                        StartStation.station_name AS start_name,
                        EndStation.station_crs AS end_crs,
                        EndStation.station_name AS end_name,
                        StartCall.service_id, StartCall.run_date
                    FROM StockSegment
                    INNER JOIN Call StartCall
                    ON StockSegment.start_call = StartCall.call_id
                    INNER JOIN Station StartStation
                    ON StartCall.station_crs = StartStation.station_crs
                    INNER JOIN Call EndCall
                    ON StockSegment.end_call = EndCall.call_id
                    INNER JOIN Station EndStation
                    ON EndCall.station_crs = EndStation.station_crs
                    INNER JOIN LegCall StartLegCall
                    On StartLegCall.dep_call_id = StartCall.call_id
                    INNER JOIN Leg
                    ON StartLegCall.leg_id = Leg.leg_id
                )
                SELECT leg_id, service_id, run_date, start_crs, start_name, end_crs, end_name, JSON_AGG(StockDetails.*) AS stocks
                FROM StockDetails
                GROUP BY leg_id, service_id, run_date, start_crs, start_name, end_crs, end_name
            )
            SELECT leg_id, JSON_AGG(StockSegments.*) AS stocks
            FROM StockSegments
            GROUP BY leg_id
        ) StockDetails
        ON StockDetails.leg_id = Leg.leg_id
    """
    if search_start is not None:
        start_string = "leg_start >= %(start)s"
    else:
        start_string = ""
    if search_end is not None:
        end_string = "leg_start < %(end)s"
    else:
        end_string = ""
    if search_start is not None or search_end is not None:
        where_string = f"\nWHERE {" AND ".join([start_string, end_string])}"
    else:
        where_string = ""
    full_statement = f"{statement}{where_string}"
    cur.execute(full_statement, {"start": search_start, "end": search_end})
    rows = cur.fetchall()
    for row in rows:
        leg_id, leg_start, services, calls, stocks, distance = row
        leg_start_time = datetime.fromisoformat(leg_start)
        services_dict = {}
        for service in services:
            service = service[0]
            service_id = service["service_id"]
            service_run_date = datetime.fromisoformat(service["run_date"])
            service_headcode = service["headcode"]
            service_start = datetime.fromisoformat(service["service_start"])
            service_operator_id = service["operator_id"]
            service_operator_name = service["operator_name"]
            service_brand_id = service["brand_id"]
            service_brand_name = service["brand_name"]
            service_power = service["power"]
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
                service_destination = ShortTrainStation(station_name, station_crs)
                service_destinations.append(service_destination)
            service_calls = []
            service_assocs = []
            for call in service["calls"]:
                call_station = ShortTrainStation(call["station_name"], call["station_crs"])
                call_platform = call["platform"]
                if call.get("plan_arr"):
                    call_plan_arr = datetime.fromisoformat(call["plan_arr"])
                else:
                    call_plan_arr = None
                if call.get("plan_dep"):
                    call_plan_dep = datetime.fromisoformat(call["plan_dep"])
                else:
                    call_plan_dep = None
                if call.get("act_arr"):
                    call_act_arr = datetime.fromisoformat(call["act_arr"])
                else:
                    call_act_arr = None
                if call.get("act_dep"):
                    call_act_dep = datetime.fromisoformat(call["act_dep"])
                else:
                    call_act_dep = None
                call_assocs = []
                if call.get("associations"):
                    for association in call["associations"]:
                        associated_type = get_or_throw(string_to_associated_type(association["associated_type"]))
                        associated_service = ShortAssociatedService(
                            association["associated_id"],
                            association["associated_run_date"],
                            associated_type
                        )
                        call_assocs.append(associated_service)
                        service_assocs.append(associated_service)
                call_mileage = call["mileage"]
                service_call = ShortCall(call_station, call_platform, call_plan_arr, call_plan_dep, call_act_arr, call_act_dep, call_assocs, call_mileage)
                service_calls.append(service_call)
            service_object = ShortTrainService(service_id, service_headcode, service_run_date, service_start, service_origins, service_destinations, service_operator_name, service_operator_id, service_brand_id, service_brand_name, service_power, service_calls, service_assocs)
            services_dict[service_id] = service_object
            leg_calls = []
            # print(calls)
            for call in calls:
                leg_call_station = ShortTrainStation(call["station_name"], call["station_crs"])
                leg_call_platform = call["platform"]
                leg_call_plan_arr = str_or_null_to_datetime(call.get("plan_arr"))
                leg_call_plan_dep = str_or_null_to_datetime(call.get("plan_dep"))
                leg_call_act_arr = str_or_null_to_datetime(call.get("act_arr"))
                leg_call_act_dep = str_or_null_to_datetime(call.get("act_dep"))
                leg_call_mileage = call.get("mileage")
                if call.get("associations"):
                    assoc = call["associations"][0]
                    assoc_id = assoc["associated_id"]
                    assoc_run_date = datetime.fromisoformat(assoc["associated_run_date"])
                    assoc_type = get_or_throw(string_to_associated_type(assoc["associated_type"]))
                    leg_call_assoc = ShortAssociatedService(assoc_id, assoc_run_date, assoc_type)
                else:
                    leg_call_assoc = None
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
                        stock_obj = StockReport(stock_class, stock_subclass, stock_number, stock_formation)
                        leg_call_stock.append(stock_obj)
                else:
                    leg_call_stock = None
                leg_call = ShortLegCall(leg_call_station, leg_call_platform, leg_call_plan_arr, leg_call_plan_dep, leg_call_act_arr, leg_call_act_dep, leg_call_assoc, leg_call_stock, leg_call_mileage)
                leg_calls.append(leg_call)
            leg_stock = []
            print(stocks)
            for report in stocks:
                segment_start_crs = report["start_crs"]
                segment_start_name = report["start_name"]
                segment_start = ShortTrainStation(segment_start_crs, segment_start_name)
                segment_end_crs = report["end_crs"]
                segment_end_name = report["end_name"]
                segment_end = ShortTrainStation(segment_end_crs, segment_end_name)
                segment_stocks = []
                for item in report["stocks"]:
                    segment_end_name = report["end_name"]
                    stock_class = new_stock.get("stock_class")
                    stock_subclass = new_stock.get("stock_subclass")
                    stock_number = new_stock.get("stock_number")
                    stock_cars = new_stock.get("stock_cars")
                    stock_distance = new_stock.get("distance")
                stock_report = ShortLegSegmentStock(segment_stocks, segment_start, segment_end, segment_mileage)
            leg_object = ShortLeg(leg_start_time, services_dict, leg_calls, leg_stock, leg_distance)
        print(leg_id)
        print(leg_start)
        print(services)
        print(calls)
        print(distance)
        print(stocks)


if __name__ == "__main__":
    conn, cur = connect()
    select_legs(cur, None, None)

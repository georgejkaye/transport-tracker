from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from re import L, search
from typing import Callable, Optional
from psycopg2._psycopg import connection, cursor

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
    Call,
    LegCall,
    TrainService,
    get_calls,
    insert_services,
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


def select_call_id_from_leg_call(call: LegCall) -> str:
    if call.plan_arr is None:
        plan_arr_string = "AND plan_arr IS NULL"
    else:
        plan_arr_string = f"AND plan_arr = '{call.plan_arr.isoformat()}'"
    if call.plan_dep is None:
        plan_dep_string = "AND plan_dep IS NULL"
    else:
        plan_dep_string = f"AND plan_dep = '{call.plan_dep.isoformat()}'"
    select_call_id_statement = f"""(
        SELECT call_id FROM Call
        WHERE service_id = '{call.service.id}'
        AND run_date = '{call.service.run_date.isoformat()}'
        AND station_crs = '{call.station.crs}'
        {plan_arr_string}
        {plan_dep_string}
    )"""
    return select_call_id_statement


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
    call_fields = ["leg_id", "call_id", "mileage"]
    call_values = []
    for call in leg.calls:
        call_values.append(
            [
                str(leg_id),
                NoEscape(select_call_id_from_leg_call(call)),
                number_or_none_to_str(call.mileage),
            ]
        )
    insert(cur, "LegCall", call_fields, call_values)
    legstock_fields = [
        "stock_class",
        "stock_subclass",
        "stock_number",
        "stock_cars",
        "start_call",
        "end_call",
        "distance",
    ]
    legstock_values = []
    for formation in leg.stock:
        stocks = formation.stock
        for stock in stocks:
            stock_class = int_or_none_to_str_or_none(stock.class_no)
            stock_subclass = int_or_none_to_str_or_none(stock.subclass_no)
            if stock.cars is None:
                stock_cars = None
            else:
                stock_cars = str(stock.cars.cars)
            stock_number = int_or_none_to_str_or_none(stock.stock_no)
            legstock_values.append(
                [
                    stock_class,
                    stock_subclass,
                    stock_number,
                    stock_cars,
                    NoEscape(select_call_id_from_leg_call(formation.calls[0])),
                    NoEscape(select_call_id_from_leg_call(formation.calls[-1])),
                    number_or_none_to_str(formation.mileage),
                ]
            )
    insert(cur, "StockSegment", legstock_fields, legstock_values)
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
        SELECT endpoint_info.service_id, endpoint_info.run_date, JSON_AGG(endpoint_info.*) AS {column_name}
        FROM endpoint_info
        GROUP BY (endpoint_info.service_id, endpoint_info.run_date)
    """


def select_legs(
    cur: cursor, search_start: Optional[datetime], search_end: Optional[datetime]
) -> list[Leg]:
    statement = f"""
        SELECT
            Leg.leg_id, (legcalls -> 0 ->> 'plan_dep')::timestamp AS leg_start,
            services, legcalls, stocks, distance
        FROM Leg
        INNER JOIN (
            WITH legcall_info AS (
                SELECT leg_id, service_id, run_date, station_crs, platform, plan_arr, plan_dep, act_arr, act_dep, legcall.mileage
                FROM LegCall
                INNER JOIN CALL
                ON LegCall.call_id = Call.call_id
                ORDER BY COALESCE(plan_arr, plan_dep) ASC
            )
            SELECT leg_id, JSON_AGG(legcall_info.*) as legcalls
            FROM legcall_info
            GROUP BY leg_id
        ) legcall_table
        ON legcall_table.leg_id = leg.leg_id
        INNER JOIN (
            SELECT LegService.leg_id, JSON_AGG(service_details) AS services
            FROM (
                SELECT DISTINCT leg.leg_id, service.service_id
                FROM Leg
                INNER JOIN Legcall
                ON leg.leg_id = legcall.leg_id
                INNER JOIN call
                ON call.call_id = legcall.call_id
                INNER JOIN service
                ON call.service_id = service.service_id AND call.run_date = service.run_date
            ) LegService
            INNER JOIN (
                WITH service_info AS (
                    SELECT Service.service_id, Service.run_date, headcode, origins, destinations, calls,
                        operator_id, brand_id, power
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
                            SELECT service_id, station_crs, platform, plan_arr, plan_dep, act_arr, act_dep
                            FROM Call
                            ORDER BY COALESCE(plan_arr, plan_dep) ASC
                        )
                        SELECT service_id, JSON_AGG(call_info.*) AS calls
                        FROM call_info
                        GROUP BY service_id
                    ) call_details
                    ON Service.service_id = call_details.service_id
                    ORDER BY calls -> 0 ->> 'plan_dep' ASC
                )
                SELECT service_id, run_date, JSON_AGG(service_info.*) AS service_details
                FROM service_info
                GROUP BY (service_id, run_date)
            ) ServiceDetails
            ON ServiceDetails.service_id = LegService.service_id
            GROUP BY LegService.leg_id
        ) LegServices
        ON LegServices.leg_id = Leg.leg_id
        INNER JOIN (
            WITH StockDetails AS (
                SELECT
                    Leg.leg_id, stock_class, stock_subclass, stock_number, stock_cars, stocksegment.distance,
                    StartStation.station_crs AS start_crs, StartStation.station_name AS start_name,
                    EndStation.station_crs AS end_crs, EndStation.station_name AS end_name
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
                On StartLegCall.call_id = StartCall.call_id
                INNER JOIN Leg
                ON StartLegCall.leg_id = Leg.leg_id
            )
            SELECT leg_id, JSON_AGG(StockDetails.*) AS stocks
            FROM StockDetails
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
    cur.execute(statement, {"start": search_start, "end": search_end})
    rows = cur.fetchall()
    for row in rows:
        leg_id, leg_start, services, calls, distance, stocks = row
        print(leg_id)
        print(leg_start)
        print(services)
        print(calls)
        print(distance)
        print(stocks)


if __name__ == "__main__":
    conn, cur = connect()
    select_legs(cur, datetime.now(), datetime.now())

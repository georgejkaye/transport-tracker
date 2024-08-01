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
    start: LegCall
    end: LegCall


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
    call_fields = ["leg_id", "call_id"]
    call_values = []
    for call in leg.calls:
        call_values.append([str(leg_id), NoEscape(select_call_id_from_leg_call(call))])
    insert(cur, "LegCall", call_fields, call_values)
    legstock_fields = [
        "stock_class",
        "stock_subclass",
        "stock_number",
        "stock_cars",
        "start_call",
        "end_call",
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
                    NoEscape(select_call_id_from_leg_call(formation.start)),
                    NoEscape(select_call_id_from_leg_call(formation.end)),
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


def select_legs(cur: cursor, search_start: datetime, search_end: datetime) -> list[Leg]:
    statement = f"""
        SELECT leg_id, service_details.services, call_details.calls, stock_details.stocks, distance
        FROM Leg
        INNER JOIN (
            WITH service_info AS (
                SELECT Service.service_id, Service.run_date, headcode, origins, destinations,
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
            )
            SELECT service_id, run_date, JSON_AGG(service_info.*) AS services
            FROM service_info
            GROUP BY (service_id, run_date)
        )
    """
    print(statement)
    # statement = f"""
    #     SELECT , origins, destinations,
    #             operator_id, brand_id, distance, call_details.calls, stock_details.stocks
    #     FROM Leg
    #     INNER JOIN Service
    #     ON Leg.service_id = Service.service_id
    #     INNER JOIN (
    #         {get_endpoint_statement(True, "origins")}
    #     ) origin_details
    #     ON Leg.service_id = origin_details.service_id
    #     AND Leg.run_date = origin_details.run_date
    #     INNER JOIN (
    #        {get_endpoint_statement(False, "destinations")}
    #     ) destination_details
    #     ON Leg.service_id = destination_details.service_id
    #     AND Leg.run_date = destination_details.run_date
    #     INNER JOIN (
    #         WITH call_info AS (
    #             SELECT leg_id, station_name, call.station_crs, platform, plan_arr,
    #                     plan_dep, act_arr, act_dep, COALESCE(plan_arr, plan_dep) AS time,
    #                     divide_id, divide_run_date, Service.headcode AS divide_headcode, divide_origins, divide_destinations
    #             FROM call
    #             INNER JOIN Station
    #             ON call.station_crs = station.station_crs
    #             LEFT JOIN Service
    #             ON divide_id = Service.service_id AND divide_run_date = Service.run_date
    #             LEFT JOIN (
    #                 {get_endpoint_statement(True, "divide_origins")}
    #             ) divide_origins
    #             ON divide_id = divide_origins.service_id
    #             AND divide_run_date = divide_origins.run_date
    #             LEFT JOIN (
    #                 {get_endpoint_statement(False, "divide_destinations")}
    #             ) divide_destinations
    #             ON divide_id = divide_destinations.service_id
    #             AND divide_run_date = divide_destinations.run_date
    #             ORDER BY time ASC
    #         )
    #         SELECT call_info.leg_id, JSON_AGG(call_info.*) AS calls
    #         FROM call_info
    #         GROUP BY leg_id
    #     ) call_details
    #     ON Leg.leg_id = call_details.leg_id
    #     INNER JOIN (
    #         WITH stock_info AS (
    #             SELECT leg_id, start_crs, start_station.station_name AS start_name,
    #                     end_crs, end_station.station_name AS end_name, stock_number,
    #                     stock_class, stock_subclass, cars
    #             FROM legstock
    #             INNER JOIN stockformation
    #             ON legstock.formation_id = stockformation.formation_id
    #             INNER JOIN station AS start_station
    #             ON start_crs = start_station.station_crs
    #             INNER JOIN station AS end_station
    #             ON end_crs = end_station.station_crs
    #         )
    #         SELECT stock_info.leg_id, JSON_AGG(stock_info.*) AS stocks
    #         FROM stock_info
    #         GROUP BY leg_id
    #     ) stock_details
    #     ON Leg.leg_id = stock_details.leg_id

    # """
    # print(statement)
    # #         WHERE leg.run_date >= %(start)s AND leg.run_date < %(end)s
    # # cur.execute(statement, {"start": search_start, "end": search_end})
    # # rows = cur.fetchall()
    # # for row in rows:
    # #     service_id, run_date, distance, calls, stocks = row
    # #     call_objects = []
    # #     for call in calls:
    # #         divide = call["divide"]
    # #         call_object = LegCall(
    # #             ShortTrainStation(call["station_name"], call["station_crs"]),
    # #             call["platform"],
    # #             str_or_null_to_datetime(call["plan_arr"]),
    # #             str_or_null_to_datetime(call["plan_dep"]),
    # #             str_or_null_to_datetime(call["act_arr"]),
    # #             str_or_null_to_datetime(call["act_dep"]),
    # #         )


if __name__ == "__main__":
    conn, cur = connect()
    print(select_legs(cur, datetime.now(), datetime.now()))

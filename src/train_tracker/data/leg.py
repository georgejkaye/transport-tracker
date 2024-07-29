from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from re import L, search
from typing import Callable, Optional
from psycopg2._psycopg import connection, cursor

from train_tracker.data.database import (
    connect,
    datetime_or_none_to_str,
    insert,
    str_or_none_to_str,
    str_or_null_to_datetime,
)
from train_tracker.data.services import (
    AssociatedService,
    Call,
    LegCall,
    TrainService,
    get_calls,
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
    start: ShortTrainStation
    end: ShortTrainStation


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


def insert_leg(conn: connection, cur: cursor, leg: Leg):
    service_fields = ["service_id", "run_date", "headcode", "operator_id", "brand_id"]
    service = leg.service
    service_values = [get_service_fields(service)]
    for join in leg.service.joins:
        service_values.append(get_service_fields(join.service))
    for divide in leg.service.divides:
        service_values.append(get_service_fields(divide.service))
    insert(cur, "Service", service_fields, service_values)
    insert_service_statement = """
        INSERT INTO Service(service_id, run_date, headcode, operator_id, brand_id)
        VALUES (%(id)s, %(rundate)s, %(headcode)s, %(operator)s, %(brand)s)
        ON CONFLICT(service_id, run_date) DO UPDATE
        SET headcode = EXCLUDED.headcode, operator_id = EXCLUDED.operator_id, brand_id = EXCLUDED.brand_id
    """
    service = leg.service
    cur.execute(
        insert_service_statement,
        {
            "id": service.id,
            "rundate": service.run_date,
            "headcode": service.headcode,
            "operator": service.operator_id,
            "brand": service.brand_id,
        },
    )
    service_endpoint_fields = ["service_id", "run_date", "station_crs", "origin"]
    service_endpoint_values = []
    for origin in service.origins:
        service_endpoint_values.append(
            [service.id, service.run_date.isoformat(), origin.crs.upper(), "true"]
        )
    for dest in service.destinations:
        service_endpoint_values.append(
            [service.id, service.run_date.isoformat(), dest.crs.upper(), "false"]
        )
    insert(cur, "ServiceEndpoint", service_endpoint_fields, service_endpoint_values)
    insert_leg_statement = """
        INSERT INTO Leg(service_id, run_date, distance, board_crs, alight_crs)
        VALUES (%(id)s, %(start)s, %(distance)s, %(board)s, %(alight)s)
        RETURNING leg_id
    """
    origin = leg.calls[0].station.crs
    destination = leg.calls[-1].station.crs
    cur.execute(
        insert_leg_statement,
        {
            "id": service.id,
            "headcode": service.headcode,
            "start": service.run_date,
            "distance": leg.distance,
            "board": origin.upper(),
            "alight": destination.upper(),
        },
    )
    leg_id = cur.fetchall()[0][0]
    calls = get_calls(service.calls, origin, destination)
    if calls is None:
        raise RuntimeError("Could not get calls")
    call_fields = [
        "leg_id",
        "run_date",
        "station_crs",
        "platform",
        "plan_arr",
        "plan_dep",
        "act_arr",
        "act_dep",
        "divide_id",
        "divide_run_date",
    ]
    call_values: list[list[str | None]] = [
        [
            str(leg_id),
            datetime_or_none_to_str(service.run_date),
            call.station.crs.upper(),
            call.platform,
            datetime_or_none_to_str(call.plan_arr),
            datetime_or_none_to_str(call.plan_dep),
            datetime_or_none_to_str(call.act_arr),
            datetime_or_none_to_str(call.act_dep),
            get_value_or_none(lambda c: c.id, call.divide),
            get_value_or_none(lambda c: c.run_date.isoformat(), call.divide),
        ]
        for call in calls
    ]
    insert(
        cur,
        "Call",
        call_fields,
        call_values,
    )
    legstock_fields = ["leg_id", "formation_id", "start_crs", "end_crs", "stock_number"]
    legstock_values = []
    for formation in leg.stock:
        stocks = formation.stock
        for stock in stocks:
            if stock.cars:
                formation_id = str(stock.cars.id)
            else:
                formation_id = "NULL"
            if stock.stock_no:
                stock_number = str(stock.stock_no)
            else:
                stock_number = "NULL"
            legstock_values.append(
                [
                    str(leg_id),
                    formation_id,
                    formation.start.crs,
                    formation.end.crs,
                    stock_number,
                ]
            )
    insert(cur, "LegStock", legstock_fields, legstock_values)
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
        SELECT Leg.service_id, headcode, Service.run_date, origins, destinations,
                operator_id, brand_id, distance, call_details.calls, stock_details.stocks
        FROM Leg
        INNER JOIN Service
        ON Leg.service_id = Service.service_id
        INNER JOIN (
            {get_endpoint_statement(True, "origins")}
        ) origin_details
        ON Leg.service_id = origin_details.service_id
        AND Leg.run_date = origin_details.run_date
        INNER JOIN (
           {get_endpoint_statement(False, "destinations")}
        ) destination_details
        ON Leg.service_id = destination_details.service_id
        AND Leg.run_date = destination_details.run_date
        INNER JOIN (
            WITH call_info AS (
                SELECT leg_id, station_name, call.station_crs, platform, plan_arr,
                        plan_dep, act_arr, act_dep, COALESCE(plan_arr, plan_dep) AS time,
                        divide_id, divide_run_date, Service.headcode AS divide_headcode, divide_origins, divide_destinations
                FROM call
                INNER JOIN Station
                ON call.station_crs = station.station_crs
                LEFT JOIN Service
                ON divide_id = Service.service_id AND divide_run_date = Service.run_date
                LEFT JOIN (
                    {get_endpoint_statement(True, "divide_origins")}
                ) divide_origins
                ON divide_id = divide_origins.service_id
                AND divide_run_date = divide_origins.run_date
                LEFT JOIN (
                    {get_endpoint_statement(False, "divide_destinations")}
                ) divide_destinations
                ON divide_id = divide_destinations.service_id
                AND divide_run_date = divide_destinations.run_date
                ORDER BY time ASC
            )
            SELECT call_info.leg_id, JSON_AGG(call_info.*) AS calls
            FROM call_info
            GROUP BY leg_id
        ) call_details
        ON Leg.leg_id = call_details.leg_id
        INNER JOIN (
            WITH stock_info AS (
                SELECT leg_id, start_crs, start_station.station_name AS start_name,
                        end_crs, end_station.station_name AS end_name, stock_number,
                        stock_class, stock_subclass, cars
                FROM legstock
                INNER JOIN stockformation
                ON legstock.formation_id = stockformation.formation_id
                INNER JOIN station AS start_station
                ON start_crs = start_station.station_crs
                INNER JOIN station AS end_station
                ON end_crs = end_station.station_crs
            )
            SELECT stock_info.leg_id, JSON_AGG(stock_info.*) AS stocks
            FROM stock_info
            GROUP BY leg_id
        ) stock_details
        ON Leg.leg_id = stock_details.leg_id

    """
    return statement
    #   WHERE leg.run_date >= %(start)s AND leg.run_date < %(end)s
    # cur.execute(statement, {"start": search_start, "end": search_end})
    # rows = cur.fetchall()
    # for row in rows:
    #     service_id, run_date, distance, calls, stocks = row
    #     call_objects = []
    #     for call in calls:
    #         divide = call["divide"]
    #         call_object = LegCall(
    #             ShortTrainStation(call["station_name"], call["station_crs"]),
    #             call["platform"],
    #             str_or_null_to_datetime(call["plan_arr"]),
    #             str_or_null_to_datetime(call["plan_dep"]),
    #             str_or_null_to_datetime(call["act_arr"]),
    #             str_or_null_to_datetime(call["act_dep"]),
    #         )


if __name__ == "__main__":
    conn, cur = connect()
    print(select_legs(cur, datetime.now(), datetime.now()))

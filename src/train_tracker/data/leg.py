from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from psycopg2._psycopg import connection, cursor

from train_tracker.data.database import datetime_or_none_to_str, insert
from train_tracker.data.services import Call, TrainService, get_calls
from train_tracker.data.stock import Stock


@dataclass
class StockReport:
    class_no: Optional[int]
    subclass_no: Optional[int]
    stock_no: Optional[int]


@dataclass
class Leg:
    service: TrainService
    origin_station: str
    destination_station: str
    distance: Decimal
    stock: list[StockReport]


def insert_leg(conn: connection, cur: cursor, leg: Leg):
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
    origin = leg.origin_station
    destination = leg.destination_station
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
        "plan_arr",
        "plan_dep",
        "act_arr",
        "act_dep",
    ]
    call_values: list[list[str | None]] = [
        [
            str(leg_id),
            datetime_or_none_to_str(service.run_date),
            call.station.crs.upper(),
            datetime_or_none_to_str(call.plan_arr),
            datetime_or_none_to_str(call.plan_dep),
            datetime_or_none_to_str(call.act_arr),
            datetime_or_none_to_str(call.act_dep),
        ]
        for call in calls
    ]
    insert(
        cur,
        "Call",
        call_fields,
        call_values,
    )
    conn.commit()

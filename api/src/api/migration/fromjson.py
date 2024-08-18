from datetime import datetime
import json
import sys
from typing import Optional
from api.data.database import connect, disconnect, insert
from psycopg2._psycopg import cursor
from api.data.leg import Leg, insert_leg, select_call_id, select_call_id_from_leg_call
from api.src.api.data.toperator import select_operator_id


def hhmm_to_datetime(run_date: datetime, hhmm: str) -> datetime:
    return datetime(
        year=run_date.year,
        month=run_date.month,
        day=run_date.day,
        hour=int(hhmm[0:2]),
        minute=int(hhmm[2:4]),
    )


def call_time_field_to_value(
    run_date: datetime, old_call: dict, parent_field: str, child_field: str
) -> Optional[str]:
    if old_call.get(parent_field) is None:
        return None
    if old_call[parent_field].get(child_field) is None:
        return None
    return hhmm_to_datetime(run_date, old_call[parent_field][child_field]).isoformat()


def call_to_values(old_call: dict, service_id: str, service_date: datetime) -> list:
    return [
        service_id,
        service_date.isoformat(),
        old_call["crs"],
        old_call["platform"],
        call_time_field_to_value(service_date, old_call, "arr", "plan"),
        call_time_field_to_value(service_date, old_call, "dep", "plan"),
        call_time_field_to_value(service_date, old_call, "arr", "act"),
        call_time_field_to_value(service_date, old_call, "dep", "act"),
    ]


def legcall_to_values(
    leg_id: str,
    service_id: str,
    service_date: datetime,
    old_call: dict,
    mileage: Optional[str],
) -> list:
    if old_call.get("dep") is None or old_call["dep"].get("plan") is None:
        plan_dep = None
    else:
        plan_dep = hhmm_to_datetime(service_date, old_call["dep"]["plan"])
    if old_call.get("arr") is None or old_call["arr"].get("plan") is None:
        plan_arr = None
    else:
        plan_arr = hhmm_to_datetime(service_date, old_call["arr"]["plan"])
    return [
        leg_id,
        select_call_id(
            service_id, service_date, old_call["crs"], plan_arr, plan_dep, True
        ),
        select_call_id(
            service_id, service_date, old_call["crs"], plan_arr, plan_dep, False
        ),
        mileage,
    ]


def insert_old_json(cur: cursor, old_json: dict):
    old_date = old_json["date"]
    service_id = old_json["uid"]
    service_date = datetime(
        year=int(old_date["year"]),
        month=int(old_date["month"]),
        day=int(old_date["day"]),
    )
    service_headcode = old_json["headcode"]
    old_operator = old_json["operator"]
    if old_operator == "West Midlands Railway":
        old_operator = "West Midlands Trains"
        service_brand_id = "WM"
    elif old_operator == "London Northwestern Railway":
        old_operator = "West Midlands Trains"
        service_brand_id = "LN"
    else:
        service_brand_id = None
    service_operator_id = select_operator_id(cur, old_operator)
    service_statement = """
        INSERT INTO Service(service_id, run_date, headcode, operator_id, brand_id)
        VALUES(%(id)s, %(date)s, %(headcode)s, %(operator)s, %(brand)s)
        ON CONFLICT DO NOTHING
    """
    cur.execute(
        service_statement,
        {
            "id": service_id,
            "date": service_date,
            "headcode": service_headcode,
            "operator": service_operator_id,
            "brand": service_brand_id,
        },
    )
    endpoint_fields = ["service_id", "run_date", "station_crs", "origin"]
    endpoint_values = []
    for old_origin in old_json["service_origins"]:
        endpoint_values.append(
            [service_id, service_date.isoformat(), old_origin["crs"], "true"]
        )
    for old_destination in old_json["service_destinations"]:
        endpoint_values.append(
            [service_id, service_date.isoformat(), old_destination["crs"], "false"]
        )
    insert(
        cur,
        "ServiceEndpoint",
        endpoint_fields,
        endpoint_values,
        "ON CONFLICT DO NOTHING",
    )
    leg_statement = """
        INSERT INTO Leg(distance) VALUES(%(distance)s)
        RETURNING leg_id
    """
    cur.execute(
        leg_statement,
        {
            "distance": int(old_json["mileage"]["miles"])
            + int(old_json["mileage"]["chains"]) / 80
        },
    )
    leg_id = str(cur.fetchall()[0][0])
    call_fields = [
        "service_id",
        "run_date",
        "station_crs",
        "platform",
        "plan_arr",
        "plan_dep",
        "act_arr",
        "act_dep",
    ]
    call_values = []
    legcall_fields = ["leg_id", "arr_call_id", "dep_call_id", "mileage"]
    legcall_values = []
    origin_call = old_json["leg_origin"]
    call_values.append(call_to_values(origin_call, service_id, service_date))
    legcall_values.append(
        legcall_to_values(leg_id, service_id, service_date, origin_call, "0")
    )
    for call in old_json["stops"]:
        call_values.append(call_to_values(call, service_id, service_date))
        legcall_values.append(
            legcall_to_values(leg_id, service_id, service_date, call, None)
        )
    destination_call = old_json["leg_destination"]
    call_values.append(call_to_values(destination_call, service_id, service_date))
    legcall_values.append(
        legcall_to_values(
            leg_id,
            service_id,
            service_date,
            destination_call,
            str(
                int(old_json["mileage"]["miles"])
                + (int(old_json["mileage"]["chains"]) / 80)
            ),
        )
    )
    insert(cur, "Call", call_fields, call_values, "ON CONFLICT DO NOTHING")
    insert(cur, "LegCall", legcall_fields, legcall_values, "ON CONFLICT DO NOTHING")
    stock_segment_fields = ["start_call", "end_call"]
    stock_segment_values = []
    start_call_id_statement = select_call_id(
        service_id,
        service_date,
        origin_call["crs"],
        None,
        hhmm_to_datetime(service_date, origin_call["dep"]["plan"]),
        False,
    )
    end_call_id_statement = select_call_id(
        service_id,
        service_date,
        destination_call["crs"],
        hhmm_to_datetime(service_date, destination_call["arr"]["plan"]),
        None,
        True,
    )
    stock_segment_values.append([start_call_id_statement, end_call_id_statement])
    insert(cur, "StockSegment", stock_segment_fields, stock_segment_values)
    stock_entry = old_json["stock"]
    if "+" in stock_entry:
        stock_entry = stock_entry.split(" + ")[0]
    stock_entry = stock_entry.split("/")[0]
    stock_entry = stock_entry.split("s ")[1]
    stock_report_fields = ["start_call", "end_call", "stock_class"]
    stock_report_values = [
        [start_call_id_statement, end_call_id_statement, stock_entry]
    ]
    insert(cur, "StockReport", stock_report_fields, stock_report_values)


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        data = json.load(f)
    (conn, cur) = connect()
    for journey in data["journeys"]:
        for leg in journey["legs"]:
            insert_old_json(cur, leg)
    conn.commit()
    disconnect(conn, cur)

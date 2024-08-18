import csv
from datetime import datetime
import sys
from typing import Optional

from api.data.database import NoEscape, connect, disconnect, insert
from api.data.stations import select_station_from_name

from api.data.toperator import select_operator_id
from psycopg2._psycopg import cursor


def call_to_values(
    service_id: str,
    service_date: datetime,
    crs: str,
    arr: datetime | None,
    dep: datetime | None,
) -> list:
    if arr is None:
        arr_string = None
    else:
        arr_string = arr.isoformat()
    if dep is None:
        dep_string = None
    else:
        dep_string = dep.isoformat()
    return [service_id, service_date.isoformat(), crs, arr_string, dep_string]


def select_call_id(
    service_id: str,
    run_date: datetime,
    station_crs: str,
    act_arr: Optional[datetime],
    act_dep: Optional[datetime],
    arr: bool,
) -> Optional[NoEscape]:
    if arr:
        field_stub = "arr"
        act = act_arr
    else:
        field_stub = "dep"
        act = act_dep
    column = f"act_{field_stub}"
    if act is None:
        condition = f"{column} IS NULL"
    else:
        condition = f"{column} = '{act.isoformat()}'"
    select_call_id_statement = f"""(
        SELECT call_id FROM Call
        WHERE service_id = '{service_id}'
        AND run_date = '{run_date.isoformat()}'
        AND station_crs = '{station_crs}'
        AND {condition}
    )"""
    return NoEscape(select_call_id_statement)


def legcall_to_values(
    leg_id: str,
    service_id: str,
    service_date: datetime,
    crs: str,
    act_arr: Optional[datetime],
    act_dep: Optional[datetime],
    mileage: Optional[str],
) -> list:
    return [
        leg_id,
        select_call_id(service_id, service_date, crs, act_arr, act_dep, True),
        select_call_id(service_id, service_date, crs, act_arr, act_dep, False),
        mileage,
    ]


def insert_old_csv_leg(cur: cursor, row: list[str]):
    id = row[0].split("uk/train/")[1].split("/")[0]
    date_components = row[1].split("/")
    date = datetime(
        year=int(date_components[2]),
        month=int(date_components[1]),
        day=int(date_components[0]),
    )
    headcode = row[2]
    toc = row[3]
    if toc == "West Midlands Railway":
        toc = "West Midlands Trains"
        service_brand_id = "WM"
    elif toc == "London Northwestern Railway":
        toc = "West Midlands Trains"
        service_brand_id = "LN"
    elif toc == "Virgin Trains":
        toc = "Avanti West Coast"
        service_brand_id = None
    elif toc == "London North East Railway":
        toc = "LNER"
        service_brand_id = None
    elif toc == "East Midlands Trains":
        toc = "East Midlands Railway"
        service_brand_id = None
    else:
        service_brand_id = None
    service_operator_id = select_operator_id(cur, toc)
    print(service_operator_id)
    origin = row[4]
    dep_time = row[5].split(":")
    dep = datetime(
        year=date.year,
        month=date.month,
        day=date.day,
        hour=int(dep_time[0]),
        minute=int(dep_time[1]),
    )
    destination = row[6]
    arr_time = row[7].split(":")
    arr = datetime(
        year=date.year,
        month=date.month,
        day=date.day,
        hour=int(arr_time[0]),
        minute=int(arr_time[1]),
    )
    miles = row[9]
    chains = row[10]
    mileage = int(miles) + int(chains) / 80
    stock = row[12].split("Class ")[1]
    print(
        f"{id} {date} {headcode} {toc} {origin} {dep} {destination} {arr} {miles} {chains} {stock}"
    )
    service_statement = """
        INSERT INTO Service(service_id, run_date, headcode, operator_id, brand_id)
        VALUES(%(id)s, %(date)s, %(headcode)s, %(operator)s, %(brand)s)
        ON CONFLICT DO NOTHING
    """
    cur.execute(
        service_statement,
        {
            "id": id,
            "date": date,
            "headcode": headcode,
            "operator": service_operator_id,
            "brand": service_brand_id,
        },
    )
    endpoint_fields = ["service_id", "run_date", "station_crs", "origin"]
    endpoint_values = []
    origin_station = select_station_from_name(cur, origin)
    if origin_station is None:
        origin_crs = input(f"Couldn't work out crs for {origin}, enter manually")
    else:
        origin_crs = origin_station.crs
    endpoint_values.append([id, date.isoformat(), origin_crs, "true"])
    destination_station = select_station_from_name(cur, destination)
    if destination_station is None:
        destination_crs = input(
            f"Couldn't work out crs for {destination}, enter manually"
        )
    else:
        destination_crs = destination_station.crs
    endpoint_values.append([id, date.isoformat(), destination_crs, "false"])
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
        {"distance": mileage},
    )
    leg_id = str(cur.fetchall()[0][0])
    call_fields = [
        "service_id",
        "run_date",
        "station_crs",
        "act_arr",
        "act_dep",
    ]
    call_values = []
    legcall_fields = ["leg_id", "arr_call_id", "dep_call_id", "mileage"]
    legcall_values = []
    call_values.append(call_to_values(id, date, origin_crs, None, dep))
    call_values.append(call_to_values(id, date, destination_crs, arr, None))
    legcall_values.append(
        legcall_to_values(leg_id, id, date, origin_crs, None, dep, "0")
    )
    legcall_values.append(
        legcall_to_values(leg_id, id, date, destination_crs, arr, None, str(mileage))
    )
    insert(cur, "Call", call_fields, call_values, "ON CONFLICT DO NOTHING")
    insert(cur, "LegCall", legcall_fields, legcall_values, "ON CONFLICT DO NOTHING")
    stock_segment_fields = ["start_call", "end_call"]
    stock_segment_values = []
    start_call_id_segment = select_call_id(id, date, origin_crs, None, dep, True)
    end_call_id_segment = select_call_id(id, date, destination_crs, arr, None, False)
    stock_segment_values.append([start_call_id_segment, end_call_id_segment])
    insert(cur, "StockSegment", stock_segment_fields, stock_segment_values)
    stock_report_fields = ["start_call", "end_call", "stock_class"]
    stock_report_values = [[start_call_id_segment, end_call_id_segment, stock]]
    insert(cur, "StockReport", stock_report_fields, stock_report_values)


if __name__ == "__main__":
    (conn, cur) = connect()
    with open(sys.argv[1]) as f:
        reader = csv.reader(f, delimiter=",")
        for row in reader:
            insert_old_csv_leg(cur, row)
    conn.commit()
    disconnect(conn, cur)

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import xml.etree.ElementTree as ET
from train_tracker.data.core import get_tag_text, make_get_request, prefix_namespace
from train_tracker.data.credentials import get_api_credentials
from train_tracker.data.database import connect, disconnect, insert
from train_tracker.data.train import (
    generate_natrail_token,
    get_kb_url,
    get_natrail_token_headers,
)
from psycopg2._psycopg import connection, cursor

from train_tracker.times import get_datetime_route, get_hourmin_string


@dataclass
class ShortTrainStation:
    name: str
    crs: str


def string_of_short_train_station(station: ShortTrainStation) -> str:
    return f"{station.name} [{station.crs}]"


@dataclass
class TrainStation:
    name: str
    crs: str
    operator: str
    brand: Optional[str]


@dataclass
class TrainServiceAtStation:
    id: str
    headcode: str
    run_date: datetime
    origins: list[ShortTrainStation]
    destinations: list[ShortTrainStation]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    operator_name: str
    operator_id: str


def short_string_of_service_at_station(service: TrainServiceAtStation):
    return f"{service.headcode} {get_multiple_short_station_string(service.origins)} to {get_multiple_short_station_string(service.destinations)}"


def string_of_service_at_station(service: TrainServiceAtStation):
    return f"{service.headcode} {get_multiple_short_station_string(service.origins)} to {get_multiple_short_station_string(service.destinations)} plan {get_hourmin_string(service.plan_dep)} act {get_hourmin_string(service.act_dep)} ({service.operator_name})"


kb_stations_namespace = "http://nationalrail.co.uk/xml/station"


def pull_stations(natrail_token: str) -> list[TrainStation]:
    kb_stations_url = get_kb_url("stations")
    headers = get_natrail_token_headers(natrail_token)
    kb_stations = make_get_request(kb_stations_url, headers=headers).text
    kb_stations_xml = ET.fromstring(kb_stations)
    stations = []
    for stn in kb_stations_xml.findall(
        prefix_namespace(kb_stations_namespace, "Station")
    ):
        station_name = get_tag_text(stn, "Name", kb_stations_namespace)
        station_crs = get_tag_text(stn, "CrsCode", kb_stations_namespace)
        station_lat = float(get_tag_text(stn, "Latitude", kb_stations_namespace))
        station_lon = float(get_tag_text(stn, "Longitude", kb_stations_namespace))
        station_operator = get_tag_text(stn, "StationOperator", kb_stations_namespace)
        if station_operator == "WM" or station_operator == "LN":
            station_brand = station_operator
            station_operator = "LM"
        else:
            station_brand = None
        station = TrainStation(
            station_name, station_crs, station_operator, station_brand
        )
        stations.append(station)
    return stations


def populate_train_station_table(
    conn: connection, cur: cursor, stations: list[TrainStation]
):
    fields = ["station_crs", "station_name", "station_operator", "station_brand"]
    values = list(
        map(
            lambda x: [x.crs, x.name, x.operator, x.brand],
            stations,
        )
    )
    insert(cur, "Station", fields, values)
    conn.commit()


def populate_train_stations(conn: connection, cur: cursor):
    natrail_credentials = get_api_credentials("NATRAIL")
    token = generate_natrail_token(natrail_credentials)
    stations = pull_stations(token)
    populate_train_station_table(conn, cur, stations)


def get_station_from_crs(cur: cursor, crs: str) -> Optional[TrainStation]:
    query = """
        SELECT station_name, station_operator, station_brand FROM Station WHERE UPPER(station_crs) = UPPER(%(crs)s)
    """
    cur.execute(query, {"crs": crs})
    rows = cur.fetchall()
    if len(rows) == 0 or len(rows) > 1:
        return None
    row = rows[0]
    return TrainStation(row[0], crs.upper(), row[1], row[2])


def get_station_from_name(cur: cursor, name: str) -> Optional[TrainStation]:
    query = """
        SELECT station_name, station_crs, station_operator, station_brand
        FROM Station
        WHERE LOWER(station_name) = LOWER(%(name)s)
    """
    cur.execute(query, {"name": name})
    rows = cur.fetchall()
    if not len(rows) == 1:
        return None
    row = rows[0]
    return TrainStation(row[0], row[1], row[2], row[3])


def get_stations_from_substring(cur: cursor, substring: str) -> list[TrainStation]:
    query = """
        SELECT station_name, station_crs, station_operator, station_brand
        FROM Station
        WHERE LOWER(station_name) LIKE '%%' || LOWER(%(subs)s) || '%%'
    """
    cur.execute(query, {"subs": substring})
    rows = cur.fetchall()
    return [TrainStation(row[0], row[1], row[2], row[3]) for row in rows]


station_endpoint = "https://api.rtt.io/api/v1/json/search"


def response_to_short_train_station(cur: cursor, data) -> ShortTrainStation:
    name = data["description"]
    station = get_station_from_name(cur, name)
    if station is None:
        print(f"No station with name {name} found. Please update the database.")
        exit(1)
    return ShortTrainStation(name, station.crs.upper())


def get_multiple_short_station_string(locs: list[ShortTrainStation]):
    string = ""
    for i, loc in enumerate(locs):
        if i == 0:
            string = loc.name
        else:
            string = f"{string} and {loc.name}"
    return string


def response_to_datetime(
    data: dict, time_field: str, run_date: datetime
) -> Optional[datetime]:
    datetime_string = data.get(time_field)
    if datetime_string is not None:
        hours = int(datetime_string[0:2])
        minutes = int(datetime_string[2:4])
        next_day = data.get(f"{time_field}NextDay")
        if next_day is not None and next_day:
            actual_datetime = run_date + timedelta(days=1, hours=hours, minutes=minutes)
        else:
            actual_datetime = run_date + timedelta(days=0, hours=hours, minutes=minutes)
        return actual_datetime
    else:
        return None


def response_to_service_at_station(cur: cursor, data: dict) -> TrainServiceAtStation:
    id = data["serviceUid"]
    headcode = data["trainIdentity"]
    operator_id = data["atocCode"]
    operator_name = data["atocName"]
    run_date = datetime.strptime(data["runDate"], "%Y-%m-%d")
    origins = [
        response_to_short_train_station(cur, origin)
        for origin in data["locationDetail"]["origin"]
    ]
    destinations = [
        response_to_short_train_station(cur, destination)
        for destination in data["locationDetail"]["destination"]
    ]
    plan_dep = response_to_datetime(
        data["locationDetail"], "gbttBookedDeparture", run_date
    )
    act_dep = response_to_datetime(
        data["locationDetail"], "realtimeDeparture", run_date
    )
    return TrainServiceAtStation(
        id,
        headcode,
        run_date,
        origins,
        destinations,
        plan_dep,
        act_dep,
        operator_name,
        operator_id,
    )


def get_services_at_station(
    cur: cursor, station: TrainStation, dt: datetime
) -> list[TrainServiceAtStation]:
    endpoint = f"{station_endpoint}/{station.crs}/{get_datetime_route(dt, True)}"
    rtt_credentials = get_api_credentials("RTT")
    response = make_get_request(endpoint, rtt_credentials)
    if not response.status_code == 200:
        return []
    data = response.json()
    if data.get("services") is None:
        return []
    services = [
        response_to_service_at_station(cur, service) for service in data["services"]
    ]
    return services


def compare_crs(a: str, b: str) -> bool:
    return a.upper() == b.upper()


if __name__ == "__main__":
    (conn, cur) = connect()
    populate_train_stations(conn, cur)
    disconnect(conn, cur)

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import xml.etree.ElementTree as ET
from api.data.core import get_tag_text, make_get_request, prefix_namespace
from api.data.credentials import get_api_credentials
from api.data.database import connect, disconnect, insert
from api.data.toperator import BrandData, OperatorData
from api.data.train import (
    generate_natrail_token,
    get_kb_url,
    get_natrail_token_headers,
)
from psycopg2._psycopg import connection, cursor

from api.times import get_datetime_route, get_hourmin_string


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


def select_station_from_crs(cur: cursor, crs: str) -> Optional[TrainStation]:
    query = """
        SELECT station_name, station_operator, station_brand FROM Station WHERE UPPER(station_crs) = UPPER(%(crs)s)
    """
    cur.execute(query, {"crs": crs})
    rows = cur.fetchall()
    if len(rows) == 0 or len(rows) > 1:
        return None
    row = rows[0]
    return TrainStation(row[0], crs.upper(), row[1], row[2])


def select_station_from_name(cur: cursor, name: str) -> Optional[TrainStation]:
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
    station = select_station_from_name(cur, name)
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
    services = []
    for service in data["services"]:
        if service["serviceType"] == "train":
            services.append(response_to_service_at_station(cur, service))
    return services


def compare_crs(a: str, b: str) -> bool:
    return a.upper() == b.upper()


@dataclass
class StationData:
    name: str
    crs: str
    operator: OperatorData
    brand: Optional[BrandData]
    img: str
    starts: int
    finishes: int
    passes: int


def select_stations(cur: cursor) -> list[StationData]:
    statement = """
        SELECT
            Station.station_name, Station.station_crs, Operator.operator_id,
            Operator.operator_name, Brand.brand_id, Brand.brand_name,
            Station.station_img,
            COALESCE(starts, 0) AS starts, COALESCE(finishes, 0) AS finishes,
            COALESCE(COALESCE(calls, 0) - COALESCE(starts, 0) - COALESCE(finishes, 0), 0) AS intermediates
        FROM Station
        LEFT JOIN (
            SELECT station_crs, COALESCE(COUNT(*), '0') AS starts
            FROM Leg
            INNER JOIN (
                SELECT
                    Leg.leg_id,
                    MIN(COALESCE(call.plan_dep, call.act_dep)) as last
                FROM Leg
                INNER JOIN LegCall
                ON Leg.leg_id = LegCall.leg_id
                INNER JOIN Call
                ON Call.call_id = LegCall.arr_call_id
                OR Call.call_id = LegCall.dep_call_id
                GROUP BY Leg.leg_id
            ) LegFirstCall
            ON LegFirstCall.leg_id = Leg.leg_id
            INNER JOIN Call
            ON LegFirstCall.last = COALESCE(Call.plan_dep, Call.act_dep)
            GROUP BY Call.station_crs
        ) StationStart
        ON Station.station_crs = StationStart.station_crs
        LEFT JOIN (
            SELECT station_crs, COUNT(*) AS finishes
            FROM Leg
            INNER JOIN (
                SELECT
                    Leg.leg_id,
                    MAX(COALESCE(call.plan_arr, call.act_arr)) as last
                FROM Leg
                INNER JOIN LegCall
                ON Leg.leg_id = LegCall.leg_id
                INNER JOIN Call
                ON Call.call_id = LegCall.arr_call_id
                OR Call.call_id = LegCall.dep_call_id
                GROUP BY Leg.leg_id
            ) LegLastCall
            ON LegLastCall.leg_id = Leg.leg_id
            INNER JOIN Call
            ON LegLastCall.last = COALESCE(Call.plan_arr, Call.act_arr)
            GROUP BY Call.station_crs
        ) StationFinish
        ON Station.station_crs = StationFinish.station_crs
        LEFT JOIN (
            SELECT station_crs, COUNT(*) AS calls
            FROM Call
            GROUP BY station_crs
        ) StationCall
        ON Station.station_crs = StationCall.station_crs
        LEFT JOIN Operator ON Operator.operator_id = Station.station_operator
        LEFT JOIN Brand ON Brand.brand_id = Station.station_brand
        ORDER BY Station.station_name ASC
    """
    cur.execute(statement)
    rows = cur.fetchall()
    stations = []
    for row in rows:
        if row[4] is None:
            brand_data = None
        else:
            brand_data = BrandData(row[4], row[5])
        data = StationData(
            row[0],
            row[1],
            OperatorData(row[2], row[3]),
            brand_data,
            row[6],
            int(row[7]),
            int(row[8]),
            int(row[9]),
        )
        stations.append(data)
    return stations


@dataclass
class LegAtStation:
    id: str
    run_date: datetime
    origin: ShortTrainStation
    destination: ShortTrainStation
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]


@dataclass
class DetailedStationData:
    name: str
    crs: str
    legs: list[LegAtStation]
    starts: int
    finishes: int
    passes: int


def select_station(station_crs: str) -> DetailedStationData:
    statement = """
        SELECT
            Station.station_crs, station_name,
            Operator.operator_id, Operator.operator_name,
            Brand.brand_id, Brand.brand_name
            StationLeg.legs,
            starts, finishes, calls
        FROM Station
        INNER JOIN Operator
        ON Station.station_operator = Operator.operator_id
        LEFT JOIN Brand
        ON Station.station_brand = Brand.brand_id
        LEFT JOIN (
            SELECT leg.leg_id, startdetails.station_crs AS start_crs, enddetails.station_crs AS end_crs, calls.calls FROM leg INNER JOIN (SELECT leg.leg_id, call.station_crs
        FROM leg
        INNER JOIN (
            SELECT leg.leg_id, MAX(COALESCE(plan_dep, plan_arr, act_dep, act_arr))
            FROM station
            INNER JOIN call
            ON call.station_crs = station.station_crs
            INNER JOIN legcall
            ON call.call_id = legcall.arr_call_id
            OR call.call_id = legcall.dep_call_id
            INNER JOIN leg
            ON legcall.leg_id = leg.leg_id
            GROUP BY leg.leg_id
        ) lasts
        ON leg.leg_id = lasts.leg_id
        INNER JOIN Call
        ON lasts.max = COALESCE(call.plan_dep, plan_arr, act_dep, act_arr)) enddetails ON leg.leg_id = enddetails.leg_id INNER JOIN (SELECT leg.leg_id, call.station_crs
        FROM leg
        INNER JOIN (
            SELECT leg.leg_id, MIN(COALESCE(plan_dep, plan_arr, act_dep, act_arr))
            FROM station
            INNER JOIN call
            ON call.station_crs = station.station_crs
            INNER JOIN legcall
            ON call.call_id = legcall.arr_call_id
            OR call.call_id = legcall.dep_call_id
            INNER JOIN leg
            ON legcall.leg_id = leg.leg_id
            GROUP BY leg.leg_id
        ) firsts
        ON leg.leg_id = firsts.leg_id
        INNER JOIN Call
        ON firsts.min = COALESCE(call.plan_dep, plan_arr, act_dep, act_arr)) startdetails ON leg.leg_id = startdetails.leg_id
INNER JOIN (SELECT leg_id, ARRAY_AGG(call.station_crs) AS calls FROM call INNER JOIN legcall ON legcall.arr_call_id = call.call_id OR legcall.dep_call_id = call.call_id GROUP BY legcall.leg_id) calls ON calls.leg_id = leg.leg_id WHERE 'WYT' = ANY(calls.calls);

        )
        WHERE station_crs = %(crs)s
    """


if __name__ == "__main__":
    (conn, cur) = connect()
    populate_train_stations(conn, cur)
    disconnect(conn, cur)

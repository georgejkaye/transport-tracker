from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from webbrowser import Opera
import xml.etree.ElementTree as ET
from api.data.core import get_tag_text, make_get_request, prefix_namespace
from api.data.credentials import get_api_credentials
from api.data.database import (
    connect,
    disconnect,
    insert,
    str_or_null_to_datetime,
)
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
    operator_code: int
    brand_code: Optional[int]


@dataclass
class TrainStationInternal:
    name: str
    crs: str
    operator: OperatorData
    brand: Optional[BrandData]


@dataclass
class TrainServiceAtStation:
    id: str
    headcode: str
    run_date: datetime
    origins: list[ShortTrainStation]
    destinations: list[ShortTrainStation]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    operator_code: str
    brand_code: str


def short_string_of_service_at_station(service: TrainServiceAtStation):
    return f"{service.headcode} {get_multiple_short_station_string(service.origins)} to {get_multiple_short_station_string(service.destinations)}"


def string_of_service_at_station(service: TrainServiceAtStation):
    return f"{service.headcode} {get_multiple_short_station_string(service.origins)} to {get_multiple_short_station_string(service.destinations)} plan {get_hourmin_string(service.plan_dep)} act {get_hourmin_string(service.act_dep)} ({service.operator_code})"


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
        station_lat = float(
            get_tag_text(stn, "Latitude", kb_stations_namespace)
        )
        station_lon = float(
            get_tag_text(stn, "Longitude", kb_stations_namespace)
        )
        station_operator = get_tag_text(
            stn, "StationOperator", kb_stations_namespace
        )
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
    fields = ["station_crs", "station_name", "operator_code", "brand_code"]
    values = list(
        map(
            lambda x: [x.crs, x.name, x.operator_code, x.brand_code],
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
        SELECT
            station_name, operator_id, brand_id FROM Station
        WHERE UPPER(station_crs) = UPPER(%(crs)s)
    """
    cur.execute(query, {"crs": crs})
    rows = cur.fetchall()
    if len(rows) == 0 or len(rows) > 1:
        return None
    row = rows[0]
    return TrainStation(row[0], crs.upper(), row[1], row[2])


def select_station_from_name(cur: cursor, name: str) -> Optional[TrainStation]:
    query = """
        SELECT station_name, station_crs, operator_code, brand_code
        FROM Station
        WHERE LOWER(station_name) = LOWER(%(name)s)
    """
    cur.execute(query, {"name": name})
    rows = cur.fetchall()
    if not len(rows) == 1:
        return None
    row = rows[0]
    return TrainStation(row[0], row[1], row[2], row[3])


def get_stations_from_substring(
    cur: cursor, substring: str
) -> list[TrainStation]:
    query = """
        SELECT station_name, station_crs, operator_id, brand_id
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
            actual_datetime = run_date + timedelta(
                days=1, hours=hours, minutes=minutes
            )
        else:
            actual_datetime = run_date + timedelta(
                days=0, hours=hours, minutes=minutes
            )
        return actual_datetime
    else:
        return None


def response_to_service_at_station(
    cur: cursor, data: dict
) -> TrainServiceAtStation:
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
    endpoint = (
        f"{station_endpoint}/{station.crs}/{get_datetime_route(dt, True)}"
    )
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
class LegAtStation:
    id: int
    origin: ShortTrainStation
    destination: ShortTrainStation
    stop_time: datetime
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]


@dataclass
class StationData:
    name: str
    crs: str
    operator: OperatorData
    brand: Optional[BrandData]
    legs: list[LegAtStation]
    img: str
    starts: int
    finishes: int
    passes: int


def select_stations(
    cur: cursor, _station_crs: Optional[str] = None
) -> list[StationData]:
    statement = """
        SELECT
            Station.station_name, Station.station_crs,
            Operator.operator_id, Operator.operator_name,
            Operator.operator_code, Operator.bg_colour AS operator_bg,
            Operator.fg_colour AS operator_fg, Brand.brand_id, Brand.brand_name,
            Brand.brand_code, Brand.bg_colour AS brand_bg,
            Brand.fg_colour AS brand_fg, LegDetails.legs, station_img,
            COALESCE(starts, 0) as starts, COALESCE(ends, 0) AS ends,
            COALESCE(calls, 0) AS calls
        FROM Station
        INNER JOIN Operator
        ON Station.operator_id = Operator.operator_id
        LEFT JOIN Brand
        ON Station.brand_id = Brand.brand_id
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
            SELECT station_crs, COUNT(*) AS ends
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
        ) StationEnd
        ON Station.station_crs = StationEnd.station_crs
        LEFT JOIN (
            SELECT station_crs, COUNT(*) AS calls
            FROM Call
            GROUP BY station_crs
        ) StationCall
        ON Station.station_crs = StationCall.station_crs
        LEFT JOIN (
            WITH legdetails AS (
                SELECT
                    Call.station_crs, LegCall.leg_id,
                    StartDetails.station_name AS start_name,
                    StartDetails.station_crs AS start_crs,
                    EndDetails.station_name AS end_name,
                    EndDetails.station_crs AS end_crs,
                    COALESCE(plan_arr, plan_dep, act_arr, act_dep) AS stop_time,
                    plan_arr, act_arr, plan_dep, act_dep
                FROM Call
                INNER JOIN LegCall
                ON Call.call_id = LegCall.arr_call_id
                OR Call.call_id = LegCall.dep_call_id
                INNER JOIN (
                    SELECT Leg.leg_id, Call.station_crs, Station.station_name
                    FROM leg
                    INNER JOIN (
                        SELECT LegCall.leg_id, MIN(COALESCE(plan_dep, plan_arr, act_dep, act_arr))
                        FROM Station
                        INNER JOIN call
                        ON Call.station_crs = Station.station_crs
                        INNER JOIN legcall
                        ON Call.call_id = LegCall.arr_call_id
                        OR Call.call_id = LegCall.dep_call_id
                        GROUP BY LegCall.leg_id
                    ) firsts
                    ON leg.leg_id = firsts.leg_id
                    INNER JOIN Call
                    ON firsts.min = COALESCE(call.plan_dep, plan_arr, act_dep, act_arr)
                    INNER JOIN Station
                    ON Call.station_crs = Station.station_crs
                ) StartDetails
                ON LegCall.leg_id = StartDetails.leg_id
                INNER JOIN (
                    SELECT Leg.leg_id, Call.station_crs, Station.station_name
                    FROM leg
                    INNER JOIN (
                        SELECT
                            LegCall.leg_id,
                            MAX(COALESCE(plan_dep, plan_arr, act_dep, act_arr))
                        FROM Station
                        INNER JOIN Call
                        ON Call.station_crs = Station.station_crs
                        INNER JOIN legcall
                        ON Call.call_id = LegCall.arr_call_id
                        OR Call.call_id = LegCall.dep_call_id
                        GROUP BY LegCall.leg_id
                    ) Lasts
                    ON Leg.leg_id = Lasts.leg_id
                    INNER JOIN Call
                    ON Lasts.max = COALESCE(plan_dep, plan_arr, act_dep, act_arr)
                    INNER JOIN Station
                    ON Call.station_crs = Station.station_crs
                ) EndDetails
                ON LegCall.leg_id = EndDetails.leg_id
                INNER JOIN (
                    SELECT
                        leg_id, ARRAY_AGG(call.station_crs) AS calls
                    FROM Call
                    INNER JOIN LegCall
                    ON LegCall.arr_call_id = Call.call_id
                    OR LegCall.dep_call_id = Call.call_id
                    GROUP BY LegCall.leg_id
                ) Calls
                ON Calls.leg_id = LegCall.leg_id
            ) SELECT
                station_crs,
                JSON_AGG(legdetails.* ORDER BY stop_time DESC) AS legs
            FROM legdetails
            GROUP BY station_crs
        ) LegDetails
        ON LegDetails.station_crs = station.station_crs
    """
    if _station_crs is not None:
        where_string = "WHERE Station.station_crs = %(crs)s"
        crs_string = _station_crs.upper()
    else:
        where_string = ""
        crs_string = ""
    order_string = "ORDER BY Station.station_name ASC"
    full_statement = f"{statement}\n{where_string}\n{order_string}"
    cur.execute(full_statement, {"crs": crs_string})
    rows = cur.fetchall()
    stations = []
    for row in rows:
        (
            station_name,
            station_crs,
            operator_id,
            operator_name,
            operator_code,
            operator_bg,
            operator_fg,
            brand_id,
            brand_name,
            brand_code,
            brand_bg,
            brand_fg,
            legs,
            station_img,
            starts,
            ends,
            calls,
        ) = row
        operator_data = OperatorData(
            operator_id, operator_code, operator_name, operator_bg, operator_fg
        )
        if brand_id is None:
            brand_data = None
        else:
            brand_data = BrandData(
                brand_id, brand_code, brand_name, brand_bg, brand_fg
            )
        leg_objects = []
        if legs is not None:
            for leg_row in legs:
                leg_data = LegAtStation(
                    leg_row["leg_id"],
                    ShortTrainStation(
                        leg_row["start_name"], leg_row["start_crs"]
                    ),
                    ShortTrainStation(leg_row["end_name"], leg_row["end_crs"]),
                    datetime.fromisoformat(leg_row["stop_time"]),
                    str_or_null_to_datetime(leg_row["plan_arr"]),
                    str_or_null_to_datetime(leg_row["act_arr"]),
                    str_or_null_to_datetime(leg_row["plan_dep"]),
                    str_or_null_to_datetime(leg_row["act_dep"]),
                )
                leg_objects.append(leg_data)
        data = StationData(
            station_name,
            station_crs,
            operator_data,
            brand_data,
            leg_objects,
            station_img,
            int(starts),
            int(ends),
            int(calls),
        )
        stations.append(data)
    return stations


def select_station(cur: cursor, station_crs: str) -> Optional[StationData]:
    result = select_stations(cur, _station_crs=station_crs)
    if result is None or len(result) != 1:
        return None
    return result[0]


if __name__ == "__main__":
    (conn, cur) = connect()
    populate_train_stations(conn, cur)
    disconnect(conn, cur)

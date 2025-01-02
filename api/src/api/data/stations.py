from decimal import Decimal
from logging.config import dictConfig
import xml.etree.ElementTree as ET

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from psycopg import Connection, Cursor

from api.data.core import get_tag_text, make_get_request, prefix_namespace
from api.data.credentials import get_api_credentials
from api.data.database import (
    connect,
    insert,
    str_or_null_to_datetime,
)
from api.data.toperator import BrandData, OperatorData
from api.data.train import (
    generate_natrail_token,
    get_kb_url,
    get_natrail_token_headers,
)
from api.times import get_datetime_route, get_hourmin_string


@dataclass
class ShortTrainStation:
    name: str
    crs: str


def string_of_short_train_station(station: ShortTrainStation) -> str:
    return f"{station.name} [{station.crs}]"


@dataclass
class TrainStationRaw:
    name: str
    crs: str
    operator: str
    brand: Optional[str]


@dataclass
class TrainStation:
    name: str
    crs: str
    operator: int
    brand: Optional[int]


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


def pull_stations(natrail_token: str) -> list[TrainStationRaw]:
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
        station = TrainStationRaw(
            station_name, station_crs, station_operator, station_brand
        )
        stations.append(station)
    return stations


def populate_train_station_table(
    conn: Connection, cur: Cursor, stations: list[TrainStationRaw]
):
    fields = ["station_crs", "station_name", "operator_code", "brand_code"]
    values = list(
        map(
            lambda x: [x.crs, x.name, x.operator, x.brand],
            stations,
        )
    )
    insert(cur, "Station", fields, values)
    conn.commit()


def populate_train_stations(conn: Connection, cur: Cursor):
    natrail_credentials = get_api_credentials("NATRAIL")
    token = generate_natrail_token(natrail_credentials)
    stations = pull_stations(token)
    populate_train_station_table(conn, cur, stations)


def select_station_from_crs(cur: Cursor, crs: str) -> Optional[TrainStation]:
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


def select_station_from_name(cur: Cursor, name: str) -> Optional[TrainStation]:
    query = """
        SELECT station_name, station_crs, operator_id, brand_id
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
    cur: Cursor, substring: str
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


def response_to_short_train_station(cur: Cursor, data) -> ShortTrainStation:
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
    cur: Cursor, data: dict
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
    cur: Cursor, station: TrainStation, dt: datetime
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
    platform: Optional[str]
    origin: ShortTrainStation
    destination: ShortTrainStation
    stop_time: datetime
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    calls_before: Optional[int]
    calls_after: Optional[int]
    operator: OperatorData
    brand: Optional[BrandData]


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
    cur: Cursor, _station_crs: Optional[str] = None
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
                    MIN(COALESCE(Call.plan_dep, Call.act_dep)) as last
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
                    MAX(COALESCE(Call.plan_arr, Call.act_arr)) as last
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
                    Call.station_crs, Call.platform, LegCall.leg_id,
                    StartDetails.station_name AS start_name,
                    StartDetails.station_crs AS start_crs,
                    EndDetails.station_name AS end_name,
                    EndDetails.station_crs AS end_crs,
                    COALESCE(plan_arr, plan_dep, act_arr, act_dep) AS stop_time,
                    plan_arr, act_arr, plan_dep, act_dep,
                    CallMetric.calls_before, CallMetric.calls_after,
                    Operator.operator_id, Operator.operator_name,
                    Operator.operator_code, Operator.bg_colour as operator_bg,
                    Operator.fg_colour as operator_fg, Brand.brand_id,
                    Brand.brand_name, Brand.brand_code, Brand.bg_colour as
                    brand_bg, Brand.fg_colour as brand_fg
                FROM Call
                INNER JOIN LegCall
                ON Call.call_id = LegCall.arr_call_id
                OR Call.call_id = LegCall.dep_call_id
                INNER JOIN Service
                ON Call.service_id = Service.service_id
                INNER JOIN Operator
                ON Service.operator_id = Operator.operator_id
                LEFT JOIN Brand
                ON Service.brand_id = Brand.brand_id
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
                    ON firsts.min = COALESCE(Call.plan_dep, plan_arr, act_dep, act_arr)
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
                        leg_id, ARRAY_AGG(Call.station_crs) AS calls
                    FROM Call
                    INNER JOIN LegCall
                    ON LegCall.arr_call_id = Call.call_id
                    OR LegCall.dep_call_id = Call.call_id
                    GROUP BY LegCall.leg_id
                ) Calls
                ON Calls.leg_id = LegCall.leg_id
                INNER JOIN (
                    WITH ThisLegCall AS (
                        SELECT
                            LegCall.leg_id, Call.call_id, Call.station_crs,
                            COALESCE(Call.plan_arr, Call.plan_dep, Call.act_arr, Call.act_dep) AS stop_time,
                            OtherCall.station_crs AS other_station,
                            COALESCE(OtherCall.plan_arr, OtherCall.plan_dep, OtherCall.act_arr, OtherCall.act_dep) AS other_stop_time
                        FROM LegCall
                        INNER JOIN Call
                        ON COALESCE(LegCall.arr_call_id, LegCall.dep_call_id) = Call.call_id
                        INNER JOIN LegCall OtherLegCall
                        ON LegCall.leg_id = OtherLegCall.leg_id
                        INNER JOIN Call OtherCall
                        ON COALESCE(OtherLegCall.arr_call_id, OtherLegCall.dep_call_id) = OtherCall.call_id
                    )
                    SELECT
                        DISTINCT ThisLegCall.leg_id, ThisLegCall.station_crs,
                        COALESCE(CallBefore.count, 0) AS calls_before,
                        COALESCE(CallAfter.count, 0) AS calls_after
                    FROM ThisLegCall
                    LEFT JOIN (
                        SELECT leg_id, station_crs, COUNT(*) FROM ThisLegCall
                        WHERE stop_time > other_stop_time
                        GROUP BY leg_id, station_crs
                    ) CallBefore
                    ON CallBefore.leg_id = ThisLegCall.leg_id
                    AND CallBefore.station_crs = ThisLegCall.station_crs
                    LEFT JOIN (
                        SELECT leg_id, station_crs, COUNT(*) FROM ThisLegCall
                        WHERE stop_time < other_stop_time
                        GROUP BY leg_id, station_crs
                    ) CallAfter
                    ON CallAfter.leg_id = ThisLegCall.leg_id
                    AND CallAfter.station_crs = ThisLegCall.station_crs
                ) CallMetric
                ON CallMetric.station_crs = Call.station_crs
                AND CallMetric.leg_id = LegCall.leg_id
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
                leg_operator = OperatorData(
                    leg_row["operator_id"],
                    leg_row["operator_code"],
                    leg_row["operator_name"],
                    leg_row["operator_bg"],
                    leg_row["operator_fg"],
                )
                if leg_row["brand_id"] is None:
                    leg_brand = None
                else:
                    leg_brand = BrandData(
                        leg_row["brand_id"],
                        leg_row["brand_code"],
                        leg_row["brand_name"],
                        leg_row["brand_bg"],
                        leg_row["brand_fg"],
                    )

                leg_data = LegAtStation(
                    leg_row["leg_id"],
                    leg_row["platform"],
                    ShortTrainStation(
                        leg_row["start_name"], leg_row["start_crs"]
                    ),
                    ShortTrainStation(leg_row["end_name"], leg_row["end_crs"]),
                    datetime.fromisoformat(leg_row["stop_time"]),
                    str_or_null_to_datetime(leg_row["plan_arr"]),
                    str_or_null_to_datetime(leg_row["act_arr"]),
                    str_or_null_to_datetime(leg_row["plan_dep"]),
                    str_or_null_to_datetime(leg_row["act_dep"]),
                    leg_row["calls_before"],
                    leg_row["calls_after"],
                    leg_operator,
                    leg_brand,
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


def select_station(cur: Cursor, station_crs: str) -> Optional[StationData]:
    result = select_stations(cur, _station_crs=station_crs)
    if result is None or len(result) != 1:
        return None
    return result[0]


def get_station_latlons_from_names(
    conn: Connection, station_names: list[str]
) -> dict[str, tuple[Decimal, Decimal]]:
    rows = conn.execute(
        "SELECT * FROM GetStationDetailsFromNames(%s::TEXT[])", [station_names]
    ).fetchall()
    if rows is None:
        raise RuntimeError(f"Could not find station with name {station_names}")
    latlon_dict = {}
    for row in rows:
        latlon_dict[row[1]] = (row[2], row[3])
    return latlon_dict


if __name__ == "__main__":
    with connect() as (conn, cur):
        get_station_latlons_from_names(
            conn,
            ["University (Birmingham)", "Shirley", "Birmingham New Street"],
        )

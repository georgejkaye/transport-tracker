import xml.etree.ElementTree as ET

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from psycopg import Connection, Cursor
from shapely import Point

from api.utils.request import make_get_request
from api.utils.credentials import get_api_credentials
from api.utils.database import (
    register_type,
    str_or_null_to_datetime,
)
from api.data.toc import BrandData, OperatorData
from api.utils.times import (
    get_datetime_route,
    get_hourmin_string,
    make_timezone_aware,
)


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
        return make_timezone_aware(actual_datetime)
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


def get_station_coordinates_from_names(
    conn: Connection, station_names: list[str]
) -> dict[str, Point]:
    rows = conn.execute(
        "SELECT * FROM GetStationDetailsFromNames(%s::TEXT[])", [station_names]
    ).fetchall()
    if rows is None:
        raise RuntimeError(f"Could not find station with name {station_names}")
    lonlat_dict = {}
    for row in rows:
        lonlat_dict[row[1]] = Point(row[2], row[3])
    return lonlat_dict


def get_station_coordinates_from_name(
    conn: Connection, station_name: str
) -> Point:
    return get_station_coordinates_from_names(conn, [station_name])[
        station_name
    ]


def get_station_lonlats_from_crses(
    conn: Connection, station_crses: list[str]
) -> dict[str, Point]:
    rows = conn.execute(
        "SELECT * FROM GetStationDetailsFromCrses(%s::TEXT[])",
        [[crs.upper() for crs in station_crses]],
    ).fetchall()
    if rows is None:
        raise RuntimeError(f"Could not find station with crs {station_crses}")
    lonlat_dict = {}
    for row in rows:
        lonlat_dict[row[0]] = Point(row[2], row[3])
    return lonlat_dict


def get_station_lonlat_from_crs(conn: Connection, station_crs: str) -> Point:
    return get_station_lonlats_from_crses(conn, [station_crs])[station_crs]


def get_station_point_from_crs_and_platform(
    conn: Connection, station_crs: str, platform: Optional[str]
) -> Optional[Point]:
    row = conn.execute(
        "SELECT * FROM GetStationPoint(%s, %s)", [station_crs.upper(), platform]
    ).fetchone()
    if row is None:
        return None
    return Point(row[1], row[0])


@dataclass
class StationPoint:
    crs: str
    name: str
    platform: Optional[str]
    point: Point


def string_of_station_point(station_point: StationPoint) -> str:
    if station_point.platform is None:
        platform_string = ""
    else:
        platform_string = f": platform {station_point.platform}"
    return f"{station_point.name}{platform_string}"


@dataclass
class StationLocation:
    platform: Optional[str]
    point: Point


@dataclass
class StationAndPlatform:
    crs: str
    platform: Optional[str]


@dataclass
class StationPointCrsSearchResult:
    crs: str
    name: str
    station_points: list[StationLocation]


def register_station_and_points(
    station_crs: str, station_name: str, station_points: list[StationLocation]
) -> StationPointCrsSearchResult:
    return StationPointCrsSearchResult(
        station_crs, station_name, station_points
    )


@dataclass
class StationPointNameSearchResult:
    crs: str
    name: str
    search_name: str
    station_points: list[StationLocation]


def register_station_name_and_points(
    station_crs: str,
    station_name: str,
    search_name: str,
    station_points: list[StationLocation],
) -> StationPointNameSearchResult:
    return StationPointNameSearchResult(
        station_crs, station_name, search_name, station_points
    )


def get_station_point_dict(
    rows: (
        list[StationPointCrsSearchResult] | list[StationPointNameSearchResult]
    ),
) -> dict[str, dict[Optional[str], StationPoint]]:
    station_point_dict = {}
    for row in rows:
        station_point_dict[row.crs] = {}
        for point in row.station_points:
            station_point_dict[row.crs][point.platform] = StationPoint(
                row.crs, row.name, point.platform, point.point
            )
    return station_point_dict


def register_station_latlon(
    platform: str, latitude: float, longitude: float
) -> StationLocation:
    return StationLocation(platform, Point(longitude, latitude))


def get_station_points(
    conn: Connection,
) -> dict[str, dict[Optional[str], StationPoint]]:
    register_type(conn, "StationLatLon", register_station_latlon)
    rows = conn.execute("SELECT GetStationPoints()").fetchall()
    return get_station_point_dict([row[0] for row in rows])


def get_station_points_from_crses(
    conn: Connection, stations: list[tuple[str, Optional[str]]]
) -> dict[str, dict[Optional[str], StationPoint]]:
    register_type(conn, "StationLatLon", register_station_latlon)
    register_type(conn, "StationAndPoints", register_station_and_points)
    rows = conn.execute(
        "SELECT GetStationPointsFromCrses(%s::StationCrsAndPlatform[])",
        [stations],
    ).fetchall()
    return get_station_point_dict([row[0] for row in rows])


def get_station_points_from_names(
    conn: Connection, stations: list[tuple[str, Optional[str]]]
) -> tuple[
    dict[str, ShortTrainStation], dict[str, dict[Optional[str], StationPoint]]
]:
    register_type(conn, "StationLatLon", register_station_latlon)
    register_type(
        conn, "StationNameAndPoints", register_station_name_and_points
    )
    rows = conn.execute(
        "SELECT GetStationPointsFromNames(%s::StationNameAndPlatform[])",
        [stations],
    ).fetchall()
    name_to_station_dict = {}
    for row in rows:
        name_to_station_dict[row[2]] = ShortTrainStation(row[1], row[0])
    return (
        name_to_station_dict,
        get_station_point_dict([row[0] for row in rows]),
    )


def get_relevant_station_points(
    station_crs: str,
    platform: Optional[str],
    station_points: dict[str, dict[Optional[str], StationPoint]],
) -> list[StationPoint]:
    crs_points = station_points[station_crs]
    if platform is None or crs_points.get(platform) is None:
        return [crs_points[key] for key in crs_points.keys()]
    return [crs_points[platform]]

from datetime import datetime
from typing import Optional

from psycopg import Connection
from psycopg.rows import class_row

from api.classes.train.operators import BrandData, OperatorData
from api.classes.train.station import (
    DbTrainStationLegPointsOutData,
    DbTrainStationOutData,
    DbTrainStationPointOutData,
    DbTrainStationPointsOutData,
    LegAtStation,
    StationData,
    TrainStationIdentifiers,
)
from api.utils.database import (
    str_or_null_to_datetime,
)


def select_station_by_crs(
    conn: Connection, crs: str
) -> Optional[DbTrainStationOutData]:
    query = """
        SELECT * FROM select_station_by_crs(%s);
    """
    with conn.cursor(row_factory=class_row(DbTrainStationOutData)) as cur:
        rows = cur.execute(query, [crs]).fetchall()
        if len(rows) == 0 or len(rows) > 1:
            return None
        return rows[0]


def select_station_by_name(
    conn: Connection, name: str
) -> Optional[DbTrainStationOutData]:
    query = """
        SELECT * FROM select_station_by_name(%s);
    """
    with conn.cursor(row_factory=class_row(DbTrainStationOutData)) as cur:
        rows = cur.execute(query, [name]).fetchall()
        if len(rows) == 0 or len(rows) > 1:
            return None
        return rows[0]


def select_stations_by_name_substring(
    conn: Connection, substring: str
) -> list[DbTrainStationOutData]:
    query = """
        SELECT * FROM select_stations_by_name_substring(%s);
    """
    with conn.cursor(row_factory=class_row(DbTrainStationOutData)) as cur:
        rows = cur.execute(query, [substring]).fetchall()
        return rows


def select_station_points_by_names_and_platforms(
    conn: Connection, substring: str
) -> list[DbTrainStationPointOutData]:
    query = """
        SELECT * FROM select_station_points_by_names_and_platforms(%s);
    """
    with conn.cursor(row_factory=class_row(DbTrainStationPointOutData)) as cur:
        rows = cur.execute(query, [substring]).fetchall()
        return rows


def compare_crs(a: str, b: str) -> bool:
    return a.upper() == b.upper()


def select_stations(
    conn: Connection, station_crs: Optional[str] = None
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
    if station_crs is not None:
        where_string = "WHERE Station.station_crs = %(crs)s"
        crs_string = station_crs.upper()
    else:
        where_string = ""
        crs_string = ""
    order_string = "ORDER BY Station.station_name ASC"
    full_statement = f"{statement}\n{where_string}\n{order_string}"
    rows = conn.execute(full_statement, {"crs": crs_string}).fetchall()
    stations: list[StationData] = []
    for row in rows:
        (
            station_name,
            current_station_crs,
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
        leg_objects: list[LegAtStation] = []
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
                    TrainStationIdentifiers(
                        leg_row["start_crs"], leg_row["start_name"]
                    ),
                    TrainStationIdentifiers(
                        leg_row["end_crs"], leg_row["start_crs"]
                    ),
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
            current_station_crs,
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


def select_station(conn: Connection, station_crs: str) -> Optional[StationData]:
    result = select_stations(conn, station_crs)
    if len(result) != 1:
        return None
    return result[0]


def select_train_station_points_by_crses(
    conn: Connection, station_crses: list[str]
) -> list[DbTrainStationPointsOutData]:
    with conn.cursor(row_factory=class_row(DbTrainStationPointsOutData)) as cur:
        return cur.execute(
            "SELECT * FROM select_train_station_points_by_crses(%s)",
            [station_crses],
        ).fetchall()


def select_train_station_points_by_name(
    conn: Connection, station_name: str
) -> Optional[DbTrainStationPointsOutData]:
    with conn.cursor(row_factory=class_row(DbTrainStationPointsOutData)) as cur:
        return cur.execute(
            "SELECT * FROM select_train_station_points_by_name(%s)",
            [station_name],
        ).fetchone()


def select_train_station_points_by_names(
    conn: Connection, station_names: list[str]
) -> list[DbTrainStationPointsOutData]:
    with conn.cursor(row_factory=class_row(DbTrainStationPointsOutData)) as cur:
        return cur.execute(
            "SELECT * FROM select_train_station_points_by_names(%s)",
            [station_names],
        ).fetchall()


def select_train_station_leg_points_by_names(
    conn: Connection, station_legs: list[list[str]]
) -> list[DbTrainStationLegPointsOutData]:
    station_leg_tuples = [(leg_calls,) for leg_calls in station_legs]
    with conn.cursor(
        row_factory=class_row(DbTrainStationLegPointsOutData)
    ) as cur:
        rows = cur.execute(
            "SELECT * FROM select_train_station_leg_points_by_name_lists(%s)",
            [station_leg_tuples],
        ).fetchall()
        conn.commit()
        return rows

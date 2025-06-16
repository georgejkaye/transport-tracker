from datetime import datetime
from typing import Optional
from psycopg import Connection
from psycopg.rows import class_row

from api.user import User
from api.classes.bus.journey import DbBusCallInData
from api.classes.bus.leg import BusLegIn, BusLegUserDetails, register_leg_types


def insert_leg(conn: Connection, users: list[User], leg: BusLegIn) -> None:
    call_tuples: list[DbBusCallInData] = []
    for call in leg.journey.calls:
        call_tuples.append(
            (
                call.index,
                call.atco,
                call.plan_arr,
                call.act_arr,
                call.plan_dep,
                call.act_dep,
            )
        )
    journey_tuple = (
        leg.journey.id,
        leg.journey.service.id,
        call_tuples,
        leg.journey.vehicle.id if leg.journey.vehicle else None,
    )
    leg_tuple = (
        journey_tuple,
        leg.board_stop_index,
        leg.alight_stop_index,
    )
    user_ids = [user.user_id for user in users]
    conn.execute(
        "SELECT InsertBusLeg(%s, %s::BusLegInData)", [user_ids, leg_tuple]
    )
    conn.commit()


def select_bus_legs(conn: Connection, user_id: int) -> list[BusLegUserDetails]:
    register_leg_types(conn)
    rows = conn.execute(
        "SELECT GetUserDetailsForBusLeg(%s)", [user_id]
    ).fetchall()
    return [row[0] for row in rows]


def select_bus_legs_by_datetime(
    conn: Connection, user_id: int, search_start: datetime, search_end: datetime
) -> list[BusLegUserDetails]:
    register_leg_types(conn)
    rows = conn.execute(
        "SELECT GetUserDetailsForBusLegsByDatetime(%s, %s, %s)",
        [user_id, search_start, search_end],
    ).fetchall()
    return [row[0] for row in rows]


def select_bus_legs_by_start_datetime(
    conn: Connection, user_id: int, search_start: datetime
) -> list[BusLegUserDetails]:
    register_leg_types(conn)
    rows = conn.execute(
        "SELECT GetUserDetailsForBusLegByStartDatetime(%s, %s)",
        [user_id, search_start],
    ).fetchall()
    return [row[0] for row in rows]


def select_bus_legs_by_end_datetime(
    conn: Connection, user_id: int, search_end: datetime
) -> list[BusLegUserDetails]:
    register_leg_types(conn)
    rows = conn.execute(
        "SELECT GetUserDetailsForBusLegByEngDatetime(%s, %s)",
        [user_id, search_end],
    ).fetchall()
    return [row[0] for row in rows]


def select_bus_leg_by_id(
    conn: Connection, user_id: int, leg_id: int
) -> Optional[BusLegUserDetails]:
    register_leg_types(conn)
    with conn.cursor(row_factory=class_row(BusLegUserDetails)) as cur:
        rows = cur.execute(
            "SELECT GetUserDetailsForBusLegsByIds(%s, %s)", [user_id, [leg_id]]
        ).fetchall()
        if len(rows) == 0:
            return None
        return rows[0]


def select_bus_legs_by_id(
    conn: Connection, user_id: int, leg_ids: list[int]
) -> list[BusLegUserDetails]:
    register_leg_types(conn)
    with conn.cursor(row_factory=class_row(BusLegUserDetails)) as cur:
        rows = cur.execute(
            "SELECT GetUserDetailsForBusLegByIds(%s, %s)", [user_id, leg_ids]
        ).fetchall()
        return rows

from datetime import datetime
from typing import Optional

from psycopg import Connection
from psycopg.rows import class_row

from api.classes.bus.journey import DbBusCallInData
from api.classes.bus.leg import BusLegIn, BusLegUserDetails
from api.classes.users.users import User


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
    with conn.cursor(row_factory=class_row(BusLegUserDetails)) as cur:
        rows = cur.execute(
            "SELECT * FROM GetUserDetailsForBusLeg(%s)", [user_id]
        ).fetchall()
        conn.commit()
        return rows


def select_bus_legs_by_datetime(
    conn: Connection, user_id: int, start_date: datetime, end_date: datetime
) -> list[BusLegUserDetails]:
    with conn.cursor(row_factory=class_row(BusLegUserDetails)) as cur:
        rows = cur.execute(
            "SELECT * FROM GetUserDetailsForBusLegsByDatetime(%s, %s, %s)",
            [user_id, start_date, end_date],
        ).fetchall()
        conn.commit()
        return rows


def select_bus_legs_by_start_datetime(
    conn: Connection, user_id: int, start_date: datetime
) -> list[BusLegUserDetails]:
    with conn.cursor(row_factory=class_row(BusLegUserDetails)) as cur:
        rows = cur.execute(
            "SELECT * FROM GetUserDetailsForBusLegByStartDatetime(%s, %s)",
            [user_id, start_date],
        ).fetchall()
        conn.commit()
        return rows


def select_bus_legs_by_end_datetime(
    conn: Connection, user_id: int, end_date: datetime
) -> list[BusLegUserDetails]:
    with conn.cursor(row_factory=class_row(BusLegUserDetails)) as cur:
        rows = cur.execute(
            "SELECT * FROM GetUserDetailsForBusLegByEngDatetime(%s, %s)",
            [user_id, end_date],
        ).fetchall()
        conn.commit()
        return rows


def select_bus_leg_by_id(
    conn: Connection, user_id: int, leg_id: int
) -> Optional[BusLegUserDetails]:
    with conn.cursor(row_factory=class_row(BusLegUserDetails)) as cur:
        rows = cur.execute(
            "SELECT * FROM GetUserDetailsForBusLegsByIds(%s, %s)",
            [user_id, [leg_id]],
        ).fetchall()
        conn.commit()
        if len(rows) == 0:
            return None
        return rows[0]


def select_bus_legs_by_id(
    conn: Connection, user_id: int, leg_ids: list[int]
) -> list[BusLegUserDetails]:
    with conn.cursor(row_factory=class_row(BusLegUserDetails)) as cur:
        rows = cur.execute(
            "SELECT * FROM GetUserDetailsForBusLegsByIds(%s, %s)",
            [user_id, leg_ids],
        ).fetchall()
        conn.commit()
        return rows

from typing import Optional

from psycopg import Connection
from psycopg.rows import class_row

from api.classes.bus.overview import (
    BusVehicleUserDetails,
)


def get_bus_vehicle_overviews_for_user(
    conn: Connection, user_id: int
) -> list[BusVehicleUserDetails]:
    with conn.cursor(row_factory=class_row(BusVehicleUserDetails)) as cur:
        rows = cur.execute(
            "SELECT * FROM GetUserDetailsForBusVehicles(%s)", [user_id]
        ).fetchall()
        conn.commit()
        return rows


def get_bus_vehicle_overview_for_user(
    conn: Connection, user_id: int, vehicle_id: int
) -> Optional[BusVehicleUserDetails]:
    with conn.cursor(row_factory=class_row(BusVehicleUserDetails)) as cur:
        row = cur.execute(
            "SELECT * FROM GetUserDetailsForBusVehicle(%s, %s)",
            [user_id, vehicle_id],
        ).fetchone()
        conn.commit()
        return row

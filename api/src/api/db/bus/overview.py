from typing import Optional
from api.classes.bus.vehicle import (
    BusVehicleUserDetails,
    register_bus_vehicle_user_details_types,
)
from psycopg import Connection
from psycopg.rows import class_row


def get_bus_vehicle_overviews_for_user(
    conn: Connection, user_id: int
) -> list[BusVehicleUserDetails]:
    register_bus_vehicle_user_details_types(conn)
    rows = conn.execute(
        "SELECT GetUserDetailsForBusVehicles(%s)", [user_id]
    ).fetchall()
    return [row[0] for row in rows]


def get_bus_vehicle_overview_for_user(
    conn: Connection, user_id: int, vehicle_id: int
) -> Optional[BusVehicleUserDetails]:
    register_bus_vehicle_user_details_types(conn)
    with conn.cursor(row_factory=class_row(BusVehicleUserDetails)) as cur:
        result = cur.execute(
            "SELECT GetUserDetailsForBusVehicle(%s, %s)", [user_id, vehicle_id]
        ).fetchone()
        if result is None:
            return None
        return result

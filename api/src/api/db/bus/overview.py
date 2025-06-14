from dataclasses import dataclass
from datetime import datetime, timedelta
from psycopg import Connection
from typing import Optional

from api.db.bus.stop import (
    BusCallStopDetails,
    register_bus_call_stop_details_types,
)
from api.db.bus.operators import (
    BusOperatorDetails,
    register_bus_operator_details_types,
)
from api.utils.database import register_type


@dataclass
class BusCallDetails:
    id: int
    call_index: int
    stop: BusCallStopDetails
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]


def register_bus_call_details(
    bus_call_id: int,
    call_index: int,
    bus_stop: BusCallStopDetails,
    plan_arr: Optional[datetime],
    act_arr: Optional[datetime],
    plan_dep: Optional[datetime],
    act_dep: Optional[datetime],
) -> BusCallDetails:
    return BusCallDetails(
        bus_call_id, call_index, bus_stop, plan_arr, act_arr, plan_dep, act_dep
    )


def register_bus_call_details_types(conn: Connection):
    register_bus_call_stop_details_types(conn)
    register_type(conn, "BusCallDetails", register_bus_call_details)


@dataclass
class BusLegServiceDetails:
    id: int
    line: str
    operator: BusOperatorDetails
    outbound_description: str
    inbound_description: str
    bg_colour: str
    fg_colour: str


def register_bus_leg_service_details(
    service_id: int,
    service_line: str,
    bus_operator: BusOperatorDetails,
    outbound_description: str,
    inbound_description: str,
    bg_colour: Optional[str],
    fg_colour: Optional[str],
) -> BusLegServiceDetails:
    return BusLegServiceDetails(
        service_id,
        service_line,
        bus_operator,
        outbound_description,
        inbound_description,
        bg_colour or "#ffffff",
        fg_colour or "#000000",
    )


def register_bus_leg_service_details_types(conn: Connection):
    register_bus_operator_details_types(conn)
    register_type(
        conn, "BusLegServiceDetails", register_bus_leg_service_details
    )


@dataclass
class BusLegUserDetails:
    id: int
    service: BusLegServiceDetails
    board: BusCallDetails
    alight: BusCallDetails
    duration: timedelta


def register_bus_leg_user_details(
    leg_id: int,
    bus_service: BusLegServiceDetails,
    leg_start: BusCallDetails,
    leg_end: BusCallDetails,
    leg_duration: timedelta,
) -> BusLegUserDetails:
    return BusLegUserDetails(
        leg_id, bus_service, leg_start, leg_end, leg_duration
    )


def register_bus_leg_user_details_types(conn: Connection):
    register_bus_leg_service_details_types(conn)
    register_bus_call_details_types(conn)
    register_type(conn, "BusLegUserDetails", register_bus_leg_user_details)


@dataclass
class BusVehicleLegDetails:
    id: int
    service: BusLegServiceDetails
    board: BusCallDetails
    alight: BusCallDetails
    duration: timedelta


def register_bus_vehicle_leg_details(
    leg_id: int,
    bus_service: BusLegServiceDetails,
    board_call: BusCallDetails,
    alight_call: BusCallDetails,
    leg_duration: timedelta,
) -> BusVehicleLegDetails:
    return BusVehicleLegDetails(
        leg_id, bus_service, board_call, alight_call, leg_duration
    )


def register_bus_vehicle_leg_details_types(conn: Connection):
    register_bus_leg_service_details_types(conn)
    register_bus_call_details_types(conn)
    register_type(
        conn, "BusVehicleLegDetails", register_bus_vehicle_leg_details
    )


@dataclass
class BusVehicleUserDetails:
    id: int
    number: str
    name: Optional[str]
    numberplate: str
    operator: BusOperatorDetails
    legs: list[BusVehicleLegDetails]
    duration: timedelta


def register_bus_vehicle_user_details(
    vehicle_id: int,
    vehicle_number: str,
    vehicle_name: Optional[str],
    vehicle_numberplate: str,
    vehicle_operator: BusOperatorDetails,
    vehicle_legs: list[BusVehicleLegDetails],
    vehicle_duration: timedelta,
) -> BusVehicleUserDetails:
    return BusVehicleUserDetails(
        vehicle_id,
        vehicle_number,
        vehicle_name,
        vehicle_numberplate,
        vehicle_operator,
        vehicle_legs,
        vehicle_duration,
    )


def register_bus_vehicle_user_details_types(conn: Connection):
    register_bus_operator_details_types(conn)
    register_bus_vehicle_leg_details_types(conn)
    register_type(
        conn, "BusVehicleUserDetails", register_bus_vehicle_user_details
    )


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
    result = conn.execute(
        "SELECT GetUserDetailsForBusVehicle(%s, %s)", [user_id, vehicle_id]
    ).fetchone()
    if result is None:
        return None
    return result[0]

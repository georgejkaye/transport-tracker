from dataclasses import dataclass
from datetime import datetime, timedelta
from api.data.bus.stop import BusCallStopDetails, register_bus_call_stop_details
from psycopg import Connection
from typing import Optional

from api.data.bus.operators import BusOperator, register_bus_operator_details
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


@dataclass
class BusServiceOverview:
    id: int
    line: str
    bg_colour: str
    fg_colour: str


def register_bus_service_details(
    service_id: int,
    service_line: str,
    bg_colour: Optional[str],
    fg_colour: Optional[str],
) -> BusServiceOverview:
    return BusServiceOverview(
        service_id, service_line, bg_colour or "#ffffff", fg_colour or "#000000"
    )


@dataclass
class BusLegOverview:
    id: int
    service: BusServiceOverview
    operator: BusOperator
    board: BusCallDetails
    alight: BusCallDetails
    duration: timedelta


def register_bus_leg_user_details(
    leg_id: int,
    bus_service: BusServiceOverview,
    bus_operator: BusOperator,
    leg_start: BusCallDetails,
    leg_end: BusCallDetails,
    leg_duration: timedelta,
) -> BusLegOverview:
    return BusLegOverview(
        leg_id, bus_service, bus_operator, leg_start, leg_end, leg_duration
    )


def register_bus_leg_overview_types(conn: Connection):
    register_type(conn, "BusCallStopDetails", register_bus_call_stop_details)
    register_type(conn, "BusCallDetails", register_bus_call_details)
    register_type(conn, "BusServiceDetails", register_bus_service_details)
    register_type(conn, "BusOperatorDetails", register_bus_operator_details)
    register_type(conn, "BusLegUserDetails", register_bus_leg_user_details)


@dataclass
class BusVehicleUserDetails:
    id: int
    number: str
    name: Optional[str]
    numberplate: str
    operator: BusOperator
    legs: list[BusLegOverview]
    duration: timedelta


def register_bus_vehicle_user_details(
    vehicle_id: int,
    vehicle_number: str,
    vehicle_name: Optional[str],
    vehicle_numberplate: str,
    vehicle_operator: BusOperator,
    vehicle_legs: list[BusLegOverview],
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


def register_bus_vehicle_overview_types(conn: Connection):
    register_bus_leg_overview_types(conn)
    register_type(
        conn, "BusVehicleUserDetails", register_bus_vehicle_user_details
    )


def get_bus_vehicle_overviews_for_user(
    conn: Connection, user_id: int
) -> list[BusVehicleUserDetails]:
    register_bus_vehicle_overview_types(conn)
    rows = conn.execute(
        "SELECT GetUserDetailsForBusVehicles(%s)", [user_id]
    ).fetchall()
    return [row[0] for row in rows]

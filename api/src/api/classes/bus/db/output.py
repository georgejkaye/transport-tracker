from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from api.classes.bus.leg import BusLegServiceDetails
from api.classes.bus.operators import BusOperatorDetails
from api.classes.bus.service import BusServiceDescription, BusServiceDetails
from psycopg import Connection
from typing import Optional

from api.utils.database import register_type


def register_bus_operator_details(
    id: int,
    name: str,
    national_code: str,
    bg_colour: Optional[str],
    fg_colour: Optional[str],
) -> BusOperatorDetails:
    return BusOperatorDetails(
        id, name, national_code, bg_colour or "#ffffff", fg_colour or "#000000"
    )


def register_bus_operator_details_types(conn: Connection) -> None:
    register_type(conn, "BusOperatorDetails", register_bus_operator_details)


def register_bus_service_details(
    bus_service_id: int,
    bus_operator: BusOperatorDetails,
    service_line: str,
    description_outbound: str,
    service_outbound_vias: list[str],
    description_inbound: str,
    service_inbound_vias: list[str],
    bg_colour: Optional[str],
    fg_colour: Optional[str],
) -> BusServiceDetails:
    return BusServiceDetails(
        bus_service_id,
        bus_operator,
        service_line,
        BusServiceDescription(description_outbound, service_outbound_vias),
        BusServiceDescription(description_inbound, service_inbound_vias),
        bg_colour or "#ffffff",
        fg_colour or "#000000",
    )


def register_bus_service_details_types(conn: Connection) -> None:
    register_bus_operator_details_types(conn)
    register_type(conn, "BusServiceDetails", register_bus_service_details)


def short_string_of_bus_service(service: BusServiceDetails) -> str:
    description = service.outbound.description
    if description == "":
        description = service.inbound.description
    return f"{service.line} {description} ({service.operator.name})"


@dataclass
class BusJourneyServiceDetails:
    id: int
    operator: BusOperatorDetails
    line: str
    bg_colour: str
    fg_colour: str


def register_bus_journey_service_details(
    bus_service_id: int,
    bus_operator: BusOperatorDetails,
    service_line: str,
    bg_colour: Optional[str],
    fg_colour: Optional[str],
) -> BusJourneyServiceDetails:
    return BusJourneyServiceDetails(
        bus_service_id,
        bus_operator,
        service_line,
        bg_colour or "#ffffff",
        fg_colour or "#000000",
    )


def register_bus_journey_service_details_types(conn: Connection) -> None:
    register_bus_operator_details_types(conn)
    register_type(
        conn, "BusJourneyServiceDetails", register_bus_journey_service_details
    )


@dataclass
class BusStopDetails:
    id: int
    atco: str
    naptan: str
    common_name: str
    landmark: str
    street: str
    crossing: Optional[str]
    indicator: Optional[str]
    bearing: str
    locality: str
    parent_locality: Optional[str]
    grandparent_locality: Optional[str]
    town: Optional[str]
    suburb: Optional[str]
    latitude: Decimal
    longitude: Decimal


def register_bus_stop_details(
    id: int,
    atco: str,
    naptan: str,
    common_name: str,
    landmark: str,
    street: str,
    crossing: Optional[str],
    indicator: Optional[str],
    bearing: str,
    locality: str,
    parent_locality: Optional[str],
    grandparent_locality: Optional[str],
    town: Optional[str],
    suburb: Optional[str],
    latitude: float,
    longitude: float,
) -> BusStopDetails:
    return BusStopDetails(
        id,
        atco,
        naptan,
        common_name,
        landmark,
        street,
        crossing,
        indicator,
        bearing,
        locality,
        parent_locality,
        grandparent_locality,
        town,
        suburb,
        Decimal(latitude),
        Decimal(longitude),
    )


def register_bus_stop_details_types(conn: Connection) -> None:
    register_type(conn, "BusStopDetails", register_bus_stop_details)


@dataclass
class BusCallStopDetails:
    id: int
    atco: str
    name: str
    locality: str
    street: Optional[str]
    indicator: Optional[str]


def register_bus_call_stop_details(
    bus_stop_id: int,
    stop_atco: str,
    stop_name: str,
    stop_locality: str,
    stop_street: Optional[str],
    stop_indicator: Optional[str],
) -> BusCallStopDetails:
    return BusCallStopDetails(
        bus_stop_id,
        stop_atco,
        stop_name,
        stop_locality,
        stop_street,
        stop_indicator,
    )


def register_bus_call_stop_details_types(conn: Connection) -> None:
    register_type(conn, "BusCallStopDetails", register_bus_call_stop_details)


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


def register_bus_call_details_types(conn: Connection) -> None:
    register_bus_call_stop_details_types(conn)
    register_type(conn, "BusCallDetails", register_bus_call_details)


@dataclass
class BusJourneyCallDetails:
    id: int
    index: int
    stop: BusCallStopDetails
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]


def register_bus_journey_call_details(
    call_id: int,
    call_index: int,
    bus_stop: BusCallStopDetails,
    plan_arr: Optional[datetime],
    act_arr: Optional[datetime],
    plan_dep: Optional[datetime],
    act_dep: Optional[datetime],
) -> BusJourneyCallDetails:
    return BusJourneyCallDetails(
        call_id, call_index, bus_stop, plan_arr, act_arr, plan_dep, act_dep
    )


def register_bus_journey_call_details_types(conn: Connection) -> None:
    register_bus_call_stop_details_types(conn)
    register_type(
        conn, "BusJourneyCallDetails", register_bus_journey_call_details
    )


@dataclass
class BusVehicleDetails:
    id: int
    operator: BusOperatorDetails
    vehicle_number: str
    bustimes_id: str
    numberplate: str
    model: Optional[str]
    livery_style: Optional[str]
    name: Optional[str]


def register_bus_vehicle_details(
    bus_vehicle_id: int,
    bus_operator: BusOperatorDetails,
    vehicle_number: str,
    bustimes_id: str,
    vehicle_numberplate: str,
    vehicle_model: str,
    vehicle_livery_style: Optional[str],
    vehicle_name: Optional[str],
) -> BusVehicleDetails:
    return BusVehicleDetails(
        bus_vehicle_id,
        bus_operator,
        vehicle_number,
        bustimes_id,
        vehicle_numberplate,
        vehicle_model,
        vehicle_livery_style,
        vehicle_name,
    )


def register_bus_vehicle_details_types(conn: Connection) -> None:
    register_bus_operator_details_types(conn)
    register_type(conn, "BusVehicleDetails", register_bus_vehicle_details)


@dataclass
class BusJourneyDetails:
    id: int
    service: BusJourneyServiceDetails
    calls: list[BusJourneyCallDetails]
    vehicle: Optional[BusVehicleDetails]


def register_bus_journey_details(
    journey_id: int,
    journey_service: BusJourneyServiceDetails,
    journey_calls: list[BusJourneyCallDetails],
    journey_vehicle: Optional[BusVehicleDetails],
) -> BusJourneyDetails:
    return BusJourneyDetails(
        journey_id, journey_service, journey_calls, journey_vehicle
    )


def register_bus_journey_details_types(conn: Connection) -> None:
    register_bus_journey_service_details_types(conn)
    register_bus_journey_call_details_types(conn)
    register_bus_vehicle_details_types(conn)
    register_type(conn, "BusJourneyDetails", register_bus_journey_details)


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


def register_bus_vehicle_leg_details_types(conn: Connection) -> None:
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


def register_bus_vehicle_user_details_types(conn: Connection) -> None:
    register_bus_operator_details_types(conn)
    register_bus_vehicle_leg_details_types(conn)
    register_type(
        conn, "BusVehicleUserDetails", register_bus_vehicle_user_details
    )

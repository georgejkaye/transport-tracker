from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from api.data.bus.journey import (
    BusCall,
    BusJourneyDetails,
    BusJourneyCallDetails,
    BusJourneyIn,
    register_bus_call,
    register_bus_journey_call_details_types,
    register_bus_journey_details,
    register_bus_journey_call_details,
    register_bus_journey_details_types,
)
from api.data.bus.operators import (
    BusOperatorDetails,
    register_bus_operator_details,
)
from api.data.bus.overview import (
    BusCallDetails,
    BusLegServiceDetails,
    register_bus_call_details_types,
    register_bus_call_stop_details,
    register_bus_leg_service_details_types,
)
from api.data.bus.service import (
    register_bus_journey_service_details,
    register_bus_service_details,
)
from api.data.bus.stop import (
    register_bus_stop_details,
)
from api.data.bus.vehicle import (
    BusVehicleDetails,
    register_bus_vehicle_details,
    register_bus_vehicle_details_types,
)
from api.user import User, UserPublic, register_user, register_user_public
from api.utils.database import register_type
from psycopg import Connection


@dataclass
class BusLegIn:
    journey: BusJourneyIn
    board_stop_index: int
    alight_stop_index: int


def insert_leg(conn: Connection, users: list[User], leg: BusLegIn):
    call_tuples = []
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


@dataclass
class BusLegUserDetails:
    id: int
    service: BusLegServiceDetails
    vehicle: BusVehicleDetails
    calls: list[BusCallDetails]
    duration: timedelta


def register_bus_leg_user_details(
    leg_id: int,
    bus_service: BusLegServiceDetails,
    bus_vehicle: BusVehicleDetails,
    calls: list[BusCallDetails],
    duration: timedelta,
) -> BusLegUserDetails:
    return BusLegUserDetails(leg_id, bus_service, bus_vehicle, calls, duration)


def register_leg_types(conn: Connection):
    register_bus_leg_service_details_types(conn)
    register_bus_vehicle_details_types(conn)
    register_bus_call_details_types(conn)
    register_type(conn, "BusLegUserDetails", register_bus_leg_user_details)


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
    rows = conn.execute(
        "SELECT GetUserDetailsForBusLegsByIds(%s, %s)", [user_id, [leg_id]]
    ).fetchall()
    if len(rows) == 0:
        return None
    return [row[0] for row in rows][0]


def select_bus_legs_by_id(
    conn: Connection, user_id: int, leg_ids: list[int]
) -> list[BusLegUserDetails]:
    register_leg_types(conn)
    rows = conn.execute(
        "SELECT GetUserDetailsForBusLegByIds(%s, %s)", [user_id, leg_ids]
    ).fetchall()
    return [row[0] for row in rows]

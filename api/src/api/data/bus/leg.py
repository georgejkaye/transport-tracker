from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from api.data.bus.journey import (
    BusCall,
    BusJourney,
    BusJourneyIn,
    register_bus_call,
    register_bus_journey,
)
from api.data.bus.operators import register_bus_operator
from api.data.bus.service import register_bus_service
from api.data.bus.stop import register_bus_stop
from api.data.bus.vehicle import BusVehicle, register_bus_vehicle
from api.user import User, UserPublic, register_user, register_user_public
from api.utils.database import register_type
from psycopg import Connection


@dataclass
class BusLegIn:
    journey: BusJourneyIn
    board_stop_index: int
    alight_stop_index: int
    vehicle: Optional[BusVehicle]


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
    )
    leg_tuple = (
        journey_tuple,
        leg.vehicle.id if leg.vehicle else None,
        leg.board_stop_index,
        leg.alight_stop_index,
    )
    user_ids = [user.user_id for user in users]
    conn.execute(
        "SELECT InsertBusLeg(%s, %s::BusLegInData)", [user_ids, leg_tuple]
    )
    conn.commit()


@dataclass
class BusLeg:
    id: int
    user: UserPublic
    journey: BusJourney
    vehicle: Optional[BusVehicle]
    calls: list[BusCall]


def register_bus_leg(
    leg_id: int,
    user: UserPublic,
    leg_journey: BusJourney,
    leg_vehicle: Optional[BusVehicle],
    leg_calls: list[BusCall],
) -> BusLeg:
    return BusLeg(leg_id, user, leg_journey, leg_vehicle, leg_calls)


def register_leg_types(conn: Connection):
    register_type(conn, "UserOutPublicData", register_user_public)
    register_type(conn, "BusOperatorOutData", register_bus_operator)
    register_type(conn, "BusStopOutData", register_bus_stop)
    register_type(conn, "BusJourneyOutData", register_bus_journey)
    register_type(conn, "BusVehicleOutData", register_bus_vehicle)
    register_type(conn, "BusLegOutData", register_bus_leg)
    register_type(conn, "BusCallOutData", register_bus_call)
    register_type(conn, "BusServiceOutData", register_bus_service)


def select_bus_legs(conn: Connection) -> list[BusLeg]:
    register_leg_types(conn)
    rows = conn.execute("SELECT GetBusLegs()").fetchall()
    return [row[0] for row in rows]


def select_bus_legs_by_datetime(
    conn: Connection, search_start: datetime, search_end: datetime
) -> list[BusLeg]:
    register_leg_types(conn)
    rows = conn.execute(
        "SELECT GetBusLegsByDatetime(%s, %s)", [search_start, search_end]
    ).fetchall()
    return [row[0] for row in rows]


def select_bus_legs_by_start_datetime(
    conn: Connection, search_start: datetime
) -> list[BusLeg]:
    register_leg_types(conn)
    rows = conn.execute(
        "SELECT GetBusLegsByStartDatetime(%s)", [search_start]
    ).fetchall()
    return [row[0] for row in rows]


def select_bus_legs_by_end_datetime(
    conn: Connection, search_end: datetime
) -> list[BusLeg]:
    register_leg_types(conn)
    rows = conn.execute(
        "SELECT GetBusLegsByEngDatetime(%s)", [search_end]
    ).fetchall()
    return [row[0] for row in rows]


def select_bus_leg_by_id(conn: Connection, id: int) -> BusLeg:
    register_leg_types(conn)
    rows = conn.execute("SELECT GetBusLegsByIds(%s)", [[id]]).fetchall()
    return [row[0] for row in rows][0]


def select_bus_legs_by_id(conn: Connection, ids: list[int]) -> list[BusLeg]:
    register_leg_types(conn)
    rows = conn.execute("SELECT GetBusLegsByIds(%s)", [ids]).fetchall()
    return [row[0] for row in rows]

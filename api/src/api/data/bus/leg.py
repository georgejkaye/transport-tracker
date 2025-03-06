from dataclasses import dataclass
from typing import Optional

from api.data.bus.service import BusJourneyIn
from api.data.bus.vehicle import BusVehicle
from psycopg import Connection


@dataclass
class BusLegIn:
    user_id: int
    journey: BusJourneyIn
    board_stop_index: int
    alight_stop_index: int
    vehicle: Optional[BusVehicle]


def insert_leg(conn: Connection, leg: BusLegIn):
    call_tuples = []
    for call in leg.journey.calls:
        call_tuples.append(
            (
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
        leg.user_id,
        journey_tuple,
        leg.vehicle.id if leg.vehicle else None,
        leg.board_stop_index,
        leg.alight_stop_index,
    )
    conn.execute("SELECT InsertBusLeg(%s::BusLegInData)", [leg_tuple])
    conn.commit()

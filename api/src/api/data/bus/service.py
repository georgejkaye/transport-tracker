from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from api.data.bus.operators import BusOperator
from api.data.bus.stop import BusStop


@dataclass
class BusService:
    id: int
    operator: BusOperator
    line: str
    outbound: str
    inbound: str
    bg_colour: Optional[str]
    fg_colour: Optional[str]


@dataclass
class BusCall:
    id: int
    stop: BusStop
    plan_arr: datetime
    plan_dep: datetime


@dataclass
class BusJourney:
    id: int
    service: BusService
    calls: list[BusCall]


@dataclass
class BusLeg:
    id: int
    journey: BusJourney
    calls: list[BusCall]

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class BustimesJourneyCall:
    stop_id: str
    stop_name: str
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]


@dataclass
class BustimesJourneyVehicle:
    bustimes_id: str
    identifier: Optional[str]
    numberplate: str


@dataclass
class BustimesJourney:
    journey_id: int
    trip_id: int
    calls: list[BustimesJourneyCall]
    vehicle: Optional[BustimesJourneyVehicle]
    block: Optional[str]

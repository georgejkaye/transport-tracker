from dataclasses import dataclass
from typing import Optional

from api.db.types.bus.journey import BusCallInData
from api.db.types.bus.operator import BusOperatorDetails
from api.db.types.bus.service import BusServiceDetails
from api.pull.bus.pages.journey.classes import BustimesJourneyVehicle


@dataclass
class BustimesJourneyData:
    calls: list[BusCallInData]
    board_call_index: int
    operator: BusOperatorDetails
    service: BusServiceDetails
    vehicle: Optional[BustimesJourneyVehicle]

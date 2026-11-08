from dataclasses import dataclass
from typing import Optional

from api.data.bus.pages.journey.classes import BustimesJourneyVehicle
from api.db.types.bus.journey import BusCallInData
from api.db.types.bus.operator import BusOperatorDetails
from api.db.types.bus.service import BusServiceDetails


@dataclass
class BustimesJourneyData:
    calls: list[BusCallInData]
    board_call_index: int
    operator: BusOperatorDetails
    service: BusServiceDetails
    vehicle: Optional[BustimesJourneyVehicle]

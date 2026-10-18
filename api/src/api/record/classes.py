from dataclasses import dataclass
from typing import Optional

from api.data.bus.operators import BusOperatorDetails
from api.data.bus.pages.journey.classes import BustimesJourneyVehicle
from api.data.bus.service import BusServiceDetails
from api.data.bus.trip import BusCallIn


@dataclass
class BustimesJourneyData:
    calls: list[BusCallIn]
    board_call_index: int
    operator: BusOperatorDetails
    service: BusServiceDetails
    vehicle: Optional[BustimesJourneyVehicle]

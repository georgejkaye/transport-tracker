from dataclasses import dataclass

from api.data.bus.operators import BusOperatorDetails
from api.data.bus.service import BusServiceDetails
from api.data.bus.trip import BusCallIn


@dataclass
class BusJourneyTimetable:
    id: int
    operator: BusOperatorDetails
    service: BusServiceDetails
    calls: list[BusCallIn]

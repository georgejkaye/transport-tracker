from dataclasses import dataclass

from api.db.types.bus.journey import BusCallInData
from api.db.types.bus.operator import BusOperatorDetails
from api.db.types.bus.service import BusServiceDetails


@dataclass
class BusJourneyTimetable:
    id: int
    operator: BusOperatorDetails
    service: BusServiceDetails
    calls: list[BusCallInData]

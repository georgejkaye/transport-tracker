from dataclasses import dataclass
from datetime import datetime


@dataclass
class BusStopDeparture:
    live: bool
    service: str
    destination: str
    dep_time: datetime
    bustimes_id: int

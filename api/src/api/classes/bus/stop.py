from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class BusStopData:
    atco: str
    naptan: str
    common_name: str
    landmark: Optional[str]
    street: str
    crossing: Optional[str]
    indicator: Optional[str]
    bearing: str
    locality: str
    parent_locality: Optional[str]
    grandparent_locality: Optional[str]
    town: Optional[str]
    suburb: Optional[str]
    latitude: Decimal
    longitude: Decimal

@dataclass
class BusStopDeparture:
    service: str
    destination: str
    dep_time: datetime
    bustimes_journey_id: int

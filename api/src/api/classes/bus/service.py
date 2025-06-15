from dataclasses import dataclass
from typing import Optional

from api.classes.bus.operators import BusOperatorDetails


@dataclass
class BusServiceDescription:
    description: str
    vias: list[str]


@dataclass
class BusServiceDetails:
    id: int
    operator: BusOperatorDetails
    line: str
    outbound: BusServiceDescription
    inbound: BusServiceDescription
    bg_colour: Optional[str]
    fg_colour: Optional[str]

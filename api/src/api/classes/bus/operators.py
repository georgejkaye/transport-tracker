from dataclasses import dataclass
from typing import Optional


@dataclass
class BusOperatorDetails:
    id: int
    name: str
    national_code: str
    bg_colour: Optional[str]
    fg_colour: Optional[str]

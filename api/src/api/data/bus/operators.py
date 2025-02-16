from dataclasses import dataclass
from typing import Optional


@dataclass
class BusOperator:
    id: int
    name: str
    code: str
    national_code: str
    bg_colour: Optional[str]
    fg_colour: Optional[str]

from dataclasses import dataclass
from typing import Optional


@dataclass
class RttScheduleOperator:
    code: Optional[str] = None
    name: Optional[str] = None

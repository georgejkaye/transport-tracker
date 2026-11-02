from dataclasses import dataclass
from typing import Optional


@dataclass
class RttPlannedActualData:
    planned: Optional[str] = None
    forecast: Optional[str] = None
    actual: Optional[str] = None

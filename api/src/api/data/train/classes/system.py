from dataclasses import dataclass
from typing import Optional


@dataclass
class RttSystemStatus:
    realtimeNetworkRail: Optional[str] = None
    rttCore: Optional[str] = None

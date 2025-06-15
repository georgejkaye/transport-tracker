from datetime import datetime
from typing import Optional


DbBusCallInData = tuple[
    int,
    str,
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
]

DbBusModelInData = tuple[Optional[str]]
DbBusVehicleInData = tuple[
    int, str, str, str, Optional[str], Optional[str], Optional[str]
]

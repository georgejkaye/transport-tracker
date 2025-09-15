from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class TrainLegCallGeometry:
    station_id: int
    station_crs: str
    station_name: str
    platform: Optional[str]
    x: Optional[Decimal]
    y: Optional[Decimal]


@dataclass
class TrainLegGeometry:
    id: int
    calls: list[TrainLegCallGeometry]
    geometry: Optional[list[tuple[Decimal, Decimal]]]

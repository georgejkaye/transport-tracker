from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class TrainLegCallGeometry:
    station_id: int
    station_crs: str
    station_name: str
    platform: Optional[str]
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    x: Optional[Decimal]
    y: Optional[Decimal]


@dataclass
class TrainLegGeometry:
    leg_id: int
    operator_id: int
    brand_id: Optional[int]
    calls: list[TrainLegCallGeometry]
    geometry: Optional[list[tuple[Decimal, Decimal]]]

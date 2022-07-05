from dataclasses import dataclass
from datetime import time
from typing import Optional
from times import PlanActTime


@dataclass
class Mileage:
    miles: Optional[int]
    chains: Optional[int]


@dataclass
class ShortLocation:
    name: str
    crs: str
    time: time


@dataclass
class Location:
    name: str
    crs: str
    tiploc: str
    arr: Optional[PlanActTime]
    dep: Optional[PlanActTime]
    platform: Optional[str]
    mileage: Mileage

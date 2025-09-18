from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from shapely import LineString, Point


@dataclass
class MapPoint:
    point: Point
    colour: str
    size: int
    tooltip: str


@dataclass
class NetworkNode:
    station_crs: str
    platform: Optional[str]


@dataclass
class NetworkNodePath:
    source: NetworkNode
    target: NetworkNode
    line: LineString


@dataclass
class LegLineCall:
    station_id: int
    station_crs: str
    station_name: str
    platform: Optional[str]
    latitude: Decimal
    longitude: Decimal
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]


@dataclass
class LegLineGeometry:
    calls: list[LegLineCall]
    line: LineString


@dataclass
class LegLine:
    board_station: str
    alight_station: str
    calls: list[LegLineCall]
    points: LineString
    colour: str
    count_lr: int
    count_rl: int


@dataclass
class CallInfo:
    pass


@dataclass
class StationInfo:
    include_counts: bool


type MarkerTextType = CallInfo | StationInfo


@dataclass
class StationCount:
    board: int
    call: int
    alight: int


@dataclass
class BoardCount:
    pass


@dataclass
class CallCount:
    pass


@dataclass
class AlightCount:
    pass


type CountType = BoardCount | CallCount | AlightCount

type StationCountDict = dict[str, tuple[LegLineCall, StationCount]]

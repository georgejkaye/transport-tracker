from dataclasses import dataclass

from shapely import LineString, Point

from api.classes.train.station import StationPoint


@dataclass
class MapPoint:
    point: Point
    colour: str
    size: int
    tooltip: str


@dataclass
class MapCall:
    station_id: int
    crs: str
    name: str


@dataclass
class LegLine:
    board_station: str
    alight_station: str
    calls: list[StationPoint]
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

type StationCountDict = dict[str, tuple[StationPoint, StationCount]]

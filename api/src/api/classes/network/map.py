from abc import abstractmethod
from dataclasses import dataclass

from shapely import LineString, Point


@dataclass
class MapPoint:
    point: Point
    colour: str
    size: int
    tooltip: str


class NetworkNode:
    @abstractmethod
    def get_id(self) -> int:
        pass


class LegNode:
    @abstractmethod
    def get_platform_points(self) -> list[Point]:
        pass


@dataclass
class NetworkNodePath[T: NetworkNode]:
    source: T
    target: T
    line: LineString


class NetworkPathPoints:
    @abstractmethod
    def get_path_points(self) -> list[list[NetworkNode]]:
        pass


@dataclass
class LegLineGeometry[T]:
    calls: list[T]
    line: LineString


@dataclass
class MarkerTextParams:
    include_times: bool = False
    include_counts: bool = False


@dataclass
class MarkerTextValues:
    boards: int
    alights: int
    calls: int


@dataclass
class LegLineCall(NetworkNode):
    @abstractmethod
    def get_call_info_text(
        self, params: MarkerTextParams, values: MarkerTextValues
    ) -> str:
        pass

    @abstractmethod
    def get_call_identifier(self) -> str:
        pass

    @abstractmethod
    def get_point(self) -> Point:
        pass


@dataclass
class LegLine[T: LegLineCall]:
    board_station: str
    alight_station: str
    calls: list[T]
    points: LineString
    colour: str
    count_lr: int
    count_rl: int


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

type StationCountDict[T] = dict[str, tuple[T, StationCount]]

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from api.network.nodes import get_node_id_from_crs_and_platform
from shapely import LineString, Point

from api.db.types.train.leg import (
    TrainLegCallPointOutData,
    TrainLegCallPointsOutData,
)


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


@dataclass
class TrainLegCallPointPointsOutData(LegLineCall):
    call: TrainLegCallPointsOutData
    point: TrainLegCallPointOutData

    def get_id(self) -> int:
        return get_node_id_from_crs_and_platform(
            self.call.station_crs, self.point.platform
        )

    def get_call_info_text(
        self, params: MarkerTextParams, values: MarkerTextValues
    ) -> str:
        def get_call_info_time_string(call_time: Optional[datetime]) -> str:
            if call_time is None:
                return "--"
            return f"{call_time.strftime('%H%M')}"

        if params.include_times:
            plan_arr_str = get_call_info_time_string(self.call.plan_arr)
            plan_dep_str = get_call_info_time_string(self.call.plan_dep)
            act_arr_str = get_call_info_time_string(self.call.act_arr)
            act_dep_str = get_call_info_time_string(self.call.act_dep)
            arr_string = f"<b>arr</b> plan {plan_arr_str} act {act_arr_str}"
            dep_string = f"<b>dep</b> plan {plan_dep_str} act {act_dep_str}"
            time_string = f"{arr_string}<br/>{dep_string}"
        else:
            time_string = ""
        return f"<h1>{self.call.station_name} ({self.call.station_crs})</h1>{time_string}"

    def get_call_identifier(self) -> str:
        return self.call.station_crs

    def get_point(self) -> Point:
        return Point(float(self.point.latitude), float(self.point.longitude))

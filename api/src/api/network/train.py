from dataclasses import dataclass
from typing import Optional

from api.network.nodes import get_node_id_from_crs_and_platform
from shapely import Point

from api.db.types.train.station import (
    TrainStationPointOutData,
    TrainStationPointsOutData,
)
from api.network.classes import (
    LegLineCall,
    MarkerTextParams,
    MarkerTextValues,
    NetworkNode,
)


def get_crs_and_platform_from_node_id(node_id: int) -> str:
    node_id_str = str(node_id)
    station_crs_str = node_id_str[1:7]
    station_platform_ind = node_id_str[7]
    station_platform_str = node_id_str[8:]
    station_crs_first_char = chr(int(station_crs_str[0:2]) + 64)
    station_crs_second_char = chr(int(station_crs_str[2:4]) + 64)
    station_crs_third_char = chr(int(station_crs_str[4:]) + 64)
    station_crs = f"{station_crs_first_char}{station_crs_second_char}{station_crs_third_char}"
    has_platform = station_platform_ind == "1"
    if not has_platform:
        platform = ""
    else:
        platform = " pl"
        is_platform_number = station_platform_str[0] == "0"
        if is_platform_number:
            platform = f"{platform} {str(int(station_platform_str[1:3]))}"
        else:
            platform = f"{platform} {chr(int(station_platform_str[1:3]) + 64)}"
        platform_suffix_str = station_platform_str[3:]
        if platform_suffix_str != "00":
            platform = f"{platform}{chr(int(platform_suffix_str) + 64)}"
    return f"{station_crs}{platform}"


@dataclass
class StationPoint(NetworkNode):
    crs: str
    platform: Optional[str]
    point: Point

    def get_id(self) -> int:
        return get_node_id_from_crs_and_platform(self.crs, self.platform)


@dataclass
class DbTrainStationPointPointsOutData(LegLineCall):
    station: TrainStationPointsOutData
    point: TrainStationPointOutData

    def get_id(self) -> int:
        return get_node_id_from_crs_and_platform(
            self.station.station_crs, self.point.platform
        )

    def get_call_info_text(
        self, params: MarkerTextParams, values: MarkerTextValues
    ) -> str:
        if params.include_counts:
            count_string = f"""
                    <b>Boards:</b> {values.boards}<br/>
                    <b>Alights:</b> {values.alights}<br/>
                    <b>Calls:</b> {values.calls}
                """
        else:
            count_string = ""
        return f"<h1>{self.station.station_name} ({self.station.station_crs})</h1>{count_string}"

    def get_call_identifier(self) -> str:
        return self.station.station_crs

    def get_point(self) -> Point:
        return Point(float(self.point.latitude), float(self.point.longitude))

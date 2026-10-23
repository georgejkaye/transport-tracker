from dataclasses import dataclass
from typing import Optional

from shapely import Point

from api.classes.network.map import (
    LegLineCall,
    MarkerTextParams,
    MarkerTextValues,
    NetworkNode,
)
from api.classes.train.network import get_node_id_from_crs_and_platform
from api.db.types.train.station import (
    TrainStationPointOutData,
    TrainStationPointsOutData,
)


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

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from shapely import Point

from api.classes.network.map import (
    LegLineCall,
    MarkerTextParams,
    MarkerTextValues,
)
from api.classes.train.network import get_node_id_from_crs_and_platform
from api.db.types.train.leg import (
    TrainLegCallPointOutData,
    TrainLegCallPointsOutData,
)


@dataclass
class StockReport:
    stock_class: Optional[int]
    stock_subclass: Optional[int]
    stock_number: Optional[int]
    stock_cars: Optional[int]


@dataclass
class DbTrainLegCallPointPointsOutData(LegLineCall):
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

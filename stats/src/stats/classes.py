from dataclasses import dataclass

import pandas as pd


@dataclass
class TrainLeg:
    leg_id: int
    board_station_name: str
    board_station_crs: str
    alight_station_name: str
    alight_station_crs: str
    start_datetime: pd.Timestamp
    operator_name: str
    operator_code: str
    distance: float
    duration: pd.Timedelta
    delay: int


@dataclass
class BusLeg:
    leg_id: int
    board_stop_name: str
    board_stop_atco: str
    alight_stop_name: str
    alight_stop_atco: str
    start_datetime: pd.Timestamp
    operator_name: str
    operator_code: str
    duration: pd.Timedelta

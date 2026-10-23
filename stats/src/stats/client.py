from typing import Any

import pandas as pd
import requests
from stats.classes import BusLeg, TrainLeg


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def invoke_transport_api_get(
        self, endpoint: str, params: dict[str, str] = {}
    ) -> requests.Response:
        return requests.get(f"{self.base_url}{endpoint}", params)

    def get_user_train_legs_for_year(self, user_id: int, year: int) -> list[TrainLeg]:
        response = self.invoke_transport_api_get(
            f"/users/{user_id}/train/legs/years/{year}"
        )
        json: list[Any] = response.json()
        return [
            TrainLeg(
                leg["leg_id"],
                leg["board_station"]["station_name"],
                leg["board_station"]["station_crs"],
                leg["alight_station"]["station_name"],
                leg["alight_station"]["station_crs"],
                pd.Timestamp(leg["start_datetime"]),
                leg["brand"]["operator_name"]
                if leg.get("brand") is not None
                else leg["operator"]["operator_name"],
                leg["brand"]["operator_code"]
                if leg.get("brand") is not None
                else leg["operator"]["operator_code"],
                float(leg["distance"]),
                pd.Timedelta(leg["duration"]),
                leg["delay"],
            )
            for leg in json
        ]

    def get_user_bus_legs_for_year(self, user_id: int, year: int) -> list[BusLeg]:
        response = self.invoke_transport_api_get(
            f"/users/{user_id}/bus/legs/years/{year}"
        )
        json: list[Any] = response.json()
        return [
            BusLeg(
                leg["leg_id"],
                f"{leg['calls'][0]['bus_stop']['stop_locality']} {leg['calls'][0]['bus_stop']['stop_name']}",
                f"{leg['calls'][0]['bus_stop']['stop_atco']}",
                f"{leg['calls'][-1]['bus_stop']['stop_locality']} {leg['calls'][-1]['bus_stop']['stop_name']}",
                f"{leg['calls'][-1]['bus_stop']['stop_atco']}",
                pd.Timestamp(leg["calls"][0]["plan_dep"]),
                leg["service"]["bus_operator"]["operator_name"],
                leg["service"]["bus_operator"]["national_operator_code"],
                pd.Timedelta(leg["duration"]),
            )
            for leg in json
        ]

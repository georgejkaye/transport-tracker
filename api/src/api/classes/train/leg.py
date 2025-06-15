from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from api.classes.train.association import AssociationType
from api.classes.train.service import TrainServiceInData
from api.classes.train.station import (
    TrainStationIdentifiers,
    get_multiple_short_station_string,
)
from api.classes.train.stock import StockReport
from api.utils.times import get_hourmin_string


@dataclass
class TrainLegCallCallInData:
    service_run_id: str
    service_run_date: datetime
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]


@dataclass
class TrainLegCallInData:
    service: TrainServiceInData
    station_crs: str
    station_name: str
    arr_call: Optional[TrainLegCallCallInData]
    dep_call: Optional[TrainLegCallCallInData]
    mileage: Optional[Decimal]
    association_type: Optional[AssociationType]


@dataclass
class TrainStockReportInData:
    stock_report: list[StockReport]
    start_call: TrainLegCallInData
    end_call: TrainLegCallInData
    mileage: Optional[Decimal]


@dataclass
class TrainLegInData:
    primary_service: TrainServiceInData
    calls: list[TrainLegCallInData]
    distance: Decimal
    stock_reports: list[TrainStockReportInData]


@dataclass
class TrainServiceAtStationToDestination:
    id: str
    headcode: str
    run_date: datetime
    origins: list[TrainStationIdentifiers]
    destinations: list[TrainStationIdentifiers]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    operator_code: str
    brand_code: str
    calls_to_destination: list[TrainLegCallInData]


def string_of_service_at_station_to_destination(
    service: TrainServiceAtStationToDestination,
) -> str:
    return f"{service.headcode} {get_multiple_short_station_string(service.origins)} to {get_multiple_short_station_string(service.destinations)} plan {get_hourmin_string(service.plan_dep)} act {get_hourmin_string(service.act_dep)} ({service.operator_code})"

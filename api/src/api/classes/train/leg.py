from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from api.classes.train.association import AssociationType
from api.classes.train.service import TrainServiceInData
from api.classes.train.stock import StockReport


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
    services: list[TrainServiceInData]
    calls: list[TrainLegCallInData]
    distance: Decimal
    stock_reports: list[TrainStockReportInData]

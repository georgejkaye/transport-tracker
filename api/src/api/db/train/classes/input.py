from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from api.db.train.classes.association import AssociationType
from api.db.train.stock import StockReport


@dataclass
class TrainServiceCallAssociatedServiceInData:
    associated_service: "TrainServiceInData"
    association: AssociationType


@dataclass
class TrainServiceCallInData:
    station_crs: str
    station_name: str
    platform: Optional[str]
    plan_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_arr: Optional[datetime]
    act_dep: Optional[datetime]
    associated_services: list[TrainServiceCallAssociatedServiceInData]
    mileage: Optional[Decimal]


@dataclass
class TrainAssociatedServiceInData:
    associated_service: "TrainServiceInData"
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    association_type: AssociationType


@dataclass
class TrainServiceInData:
    unique_identifier: str
    run_date: datetime
    headcode: str
    origin_names: list[str]
    destination_names: list[str]
    operator_code: str
    brand_code: Optional[str]
    power: Optional[str]
    calls: list[TrainServiceCallInData]


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
    station_crs: str
    station_name: str
    arr_call: Optional[TrainLegCallCallInData]
    dep_call: Optional[TrainLegCallCallInData]
    mileage: Optional[Decimal]
    association_type: Optional[AssociationType]


@dataclass
class TrainStockReportCallInData:
    service_uid: str
    service_run_date: datetime
    station_crs: str
    plan: datetime
    act: datetime


@dataclass
class TrainStockReportInData:
    stock_report: list[StockReport]
    start_call: TrainStockReportCallInData
    end_call: TrainStockReportCallInData
    mileage: Optional[Decimal]


@dataclass
class TrainLegInData:
    services: list[TrainServiceInData]
    calls: list[TrainLegCallInData]
    distance: Decimal
    stock_reports: list[TrainStockReportInData]

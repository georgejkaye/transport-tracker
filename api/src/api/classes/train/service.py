from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from api.classes.train.association import AssociationType


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
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    associated_services: list[TrainServiceCallAssociatedServiceInData]
    mileage: Optional[Decimal]


@dataclass
class TrainServiceInData:
    unique_identifier: str
    run_date: datetime
    headcode: str
    origin_names: list[str]
    destination_names: list[str]
    operator_id: int
    brand_id: Optional[int]
    power: Optional[str]
    calls: list[TrainServiceCallInData]
    associated_services: list["TrainAssociatedServiceInData"]


@dataclass
class TrainAssociatedServiceInData:
    associated_service: TrainServiceInData
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    association_type: AssociationType


###
# DB input
###

DbTrainServiceInData = tuple[
    str, datetime, str, int, Optional[int], Optional[str]
]

DbTrainServiceEndpointInData = tuple[str, datetime, str, bool]

DbTrainCallInData = tuple[
    str,
    datetime,
    str,
    Optional[str],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[Decimal],
]

DbTrainAssociatedServiceInData = tuple[
    str,
    datetime,
    str,
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    str,
    datetime,
    int,
]


@dataclass
class RttLocationTag:
    mileage: Optional[Decimal]
    crs: str
    gbtt_arr: Optional[datetime]
    gbtt_dep: Optional[datetime]

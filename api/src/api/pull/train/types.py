from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from api.classes.train import association
from api.db.types.train.leg import TrainLegCallInData


@dataclass
class TrainStationIdentifiers:
    crs: str
    name: str


@dataclass
class RttStationService:
    id: str
    headcode: str
    run_date: datetime
    origins: list[TrainStationIdentifiers]
    destinations: list[TrainStationIdentifiers]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    operator_code: str
    brand_code: str


@dataclass
class RttStationServiceToDestination:
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


@dataclass
class RttLocationTag:
    mileage: Optional[Decimal]
    crs: str
    gbtt_arr: Optional[datetime]
    gbtt_dep: Optional[datetime]


@dataclass
class RttServiceCall:
    station_crs: str
    station_name: str
    platform: Optional[str]
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    associated_services: list["RttCallAssociatedService"]
    mileage: Optional[Decimal]


@dataclass
class RttService:
    service_uid: str
    run_date: datetime
    headcode: str
    origins: list[str]
    destinations: list[str]
    operator_id: int
    brand_id: Optional[int]
    power: Optional[str]
    calls: list[RttServiceCall]
    associated_services: list["RttServiceAssociatedService"]


@dataclass
class RttCallAssociatedService:
    service_uid: str
    service_run_date: datetime
    association: association.AssociationType
    # None where necessary to avoid loops
    service: Optional[RttService]


@dataclass
class RttServiceAssociatedService:
    service: RttService
    call: RttServiceCall
    association: association.AssociationType

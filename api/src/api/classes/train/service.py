from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from psycopg import Connection

from api.classes.train.association import AssociationType
from api.classes.train.operators import (
    BrandData,
    OperatorData,
)
from api.classes.train.station import (
    TrainStationIdentifiers,
    register_short_train_station_types,
)
from api.utils.database import register_type


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

##
# DB output
##


@dataclass
class ShortAssociatedService:
    service_id: str
    service_run_date: datetime
    association: str


def register_short_associated_service_types(conn: Connection) -> None:
    register_type(conn, "TrainAssociatedServiceOutData", ShortAssociatedService)


@dataclass
class ShortCall:
    station: TrainStationIdentifiers
    platform: Optional[str]
    plan_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_arr: Optional[datetime]
    act_dep: Optional[datetime]
    assocs: list[ShortAssociatedService]
    mileage: Optional[Decimal]


def register_short_call_types(conn: Connection) -> None:
    register_short_train_station_types(conn)
    register_short_associated_service_types(conn)
    register_type(conn, "TrainCallOutData", ShortCall)


@dataclass
class ShortTrainService:
    service_id: str
    headcode: str
    run_date: datetime
    service_start: datetime
    origins: list[TrainStationIdentifiers]
    destinations: list[TrainStationIdentifiers]
    operator: OperatorData
    brand: Optional[BrandData]
    power: Optional[str]
    calls: list[ShortCall]
    assocs: list[ShortAssociatedService]


def register_service_data(
    service_id: str,
    service_run_date: datetime,
    service_headcode: str,
    service_start: datetime,
    service_origins: list[TrainStationIdentifiers],
    service_destinations: list[TrainStationIdentifiers],
    service_operator: OperatorData,
    service_brand: Optional[BrandData],
    service_calls: list[ShortCall],
    service_assocs: list[ShortAssociatedService],
) -> ShortTrainService:
    return ShortTrainService(
        service_id,
        service_headcode,
        service_run_date,
        service_start,
        service_origins,
        service_destinations,
        service_operator,
        service_brand,
        None,
        service_calls,
        service_assocs,
    )


def register_short_train_service_types(conn: Connection) -> None:
    register_short_train_station_types(conn)
    register_short_call_types(conn)
    register_short_associated_service_types(conn)
    register_type(conn, "TrainServiceOutData", ShortTrainService)


@dataclass
class RttLocationTag:
    mileage: Optional[Decimal]
    crs: str
    gbtt_arr: Optional[datetime]
    gbtt_dep: Optional[datetime]

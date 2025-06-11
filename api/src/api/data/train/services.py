from ast import Call
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from api.data.train.association import AssociationType
from api.utils.database import register_type
from bs4 import BeautifulSoup, Tag
from psycopg import Connection

from api.utils.request import get_soup, make_get_request
from api.utils.credentials import get_api_credentials
from api.utils.mileage import miles_and_chains_to_miles
from api.data.train.stations import (
    TrainLegCallStationInData,
    register_short_train_station_types,
)
from api.data.train.toc import (
    BrandData,
    OperatorData,
    register_brand_data_types,
)
from api.utils.times import (
    change_timezone,
    get_datetime_route,
    make_timezone_aware,
)


@dataclass
class ShortAssociatedService:
    service_id: str
    service_run_date: datetime
    association: str


def register_assoc_data(
    assoc_service_id: str, assoc_service_run_date: datetime, assoc_type: str
):
    return ShortAssociatedService(
        assoc_service_id, assoc_service_run_date, assoc_type
    )


def register_short_associated_service_types(conn: Connection):
    register_type(conn, "TrainAssociatedServiceOutData", register_assoc_data)


@dataclass
class ShortCall:
    station: TrainLegCallStationInData
    platform: Optional[str]
    plan_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_arr: Optional[datetime]
    act_dep: Optional[datetime]
    assocs: list[ShortAssociatedService]
    mileage: Optional[Decimal]


def register_call_data(
    station: TrainLegCallStationInData,
    platform: str,
    plan_arr: datetime,
    act_arr: datetime,
    plan_dep: datetime,
    act_dep: datetime,
    assocs: list[ShortAssociatedService],
    mileage: Decimal,
):
    return ShortCall(
        station,
        platform,
        change_timezone(plan_arr),
        change_timezone(act_arr),
        change_timezone(plan_dep),
        change_timezone(act_dep),
        assocs,
        mileage,
    )


def register_short_call_types(conn: Connection):
    register_short_train_station_types(conn)
    register_short_associated_service_types(conn)
    register_type(conn, "TrainCallOutData", register_call_data)


@dataclass
class ShortTrainService:
    service_id: str
    headcode: str
    run_date: datetime
    service_start: datetime
    origins: list[TrainLegCallStationInData]
    destinations: list[TrainLegCallStationInData]
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
    service_origins: list[TrainLegCallStationInData],
    service_destinations: list[TrainLegCallStationInData],
    service_operator: OperatorData,
    service_brand: Optional[BrandData],
    service_calls: list[ShortCall],
    service_assocs: list[ShortAssociatedService],
):
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


def register_short_train_service_types(conn: Connection):
    register_short_train_station_types(conn)
    register_brand_data_types(conn)
    register_short_call_types(conn)
    register_short_associated_service_types(conn)
    register_type(conn, "TrainServiceOutData", register_service_data)


ServiceIdentifier = tuple[str, datetime]

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from api.classes.train.station import TrainStationIdentifiers
from api.classes.train.stock import StockReport
from api.utils.database import register_type
from api.utils.times import change_timezone
from psycopg import Connection


@dataclass
class OperatorData:
    id: int
    code: str
    name: str
    bg: Optional[str]
    fg: Optional[str]


def register_operator_data(
    operator_id: int,
    operator_code: str,
    operator_name: str,
    operator_bg: str,
    operator_fg: str,
) -> OperatorData:
    return OperatorData(
        operator_id, operator_code, operator_name, operator_bg, operator_fg
    )


@dataclass
class BrandData:
    id: int
    code: str
    name: str
    bg: Optional[str]
    fg: Optional[str]


def register_brand_data(
    brand_id: int,
    brand_code: str,
    brand_name: str,
    brand_bg: str,
    brand_fg: str,
) -> BrandData:
    return BrandData(brand_id, brand_code, brand_name, brand_bg, brand_fg)


def register_brand_data_types(conn: Connection) -> None:
    register_type(conn, "OutBrandData", register_brand_data)


def register_station_data(
    station_crs: str, station_name: str
) -> TrainStationIdentifiers:
    return TrainStationIdentifiers(station_crs, station_name)


def register_short_train_station_types(conn: Connection) -> None:
    register_type(conn, "TrainStationOutData", register_station_data)


@dataclass
class LegAtStation:
    id: int
    platform: Optional[str]
    origin: TrainStationIdentifiers
    destination: TrainStationIdentifiers
    stop_time: datetime
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    calls_before: Optional[int]
    calls_after: Optional[int]
    operator: OperatorData
    brand: Optional[BrandData]


@dataclass
class StationData:
    name: str
    crs: str
    operator: OperatorData
    brand: Optional[BrandData]
    legs: list[LegAtStation]
    img: str
    starts: int
    finishes: int
    passes: int


@dataclass
class ShortAssociatedService:
    service_id: str
    service_run_date: datetime
    association: str


def register_assoc_data(
    assoc_service_id: str, assoc_service_run_date: datetime, assoc_type: str
) -> ShortAssociatedService:
    return ShortAssociatedService(
        assoc_service_id, assoc_service_run_date, assoc_type
    )


def register_short_associated_service_types(conn: Connection) -> None:
    register_type(conn, "TrainAssociatedServiceOutData", register_assoc_data)


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


def register_call_data(
    station: TrainStationIdentifiers,
    platform: str,
    plan_arr: datetime,
    act_arr: datetime,
    plan_dep: datetime,
    act_dep: datetime,
    assocs: list[ShortAssociatedService],
    mileage: Decimal,
) -> ShortCall:
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


def register_short_call_types(conn: Connection) -> None:
    register_short_train_station_types(conn)
    register_short_associated_service_types(conn)
    register_type(conn, "TrainCallOutData", register_call_data)


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
    register_brand_data_types(conn)
    register_short_call_types(conn)
    register_short_associated_service_types(conn)
    register_type(conn, "TrainServiceOutData", register_service_data)


def register_stock_report(
    stock_class: int, stock_subclass: int, stock_number: int, stock_cars: int
) -> StockReport:
    return StockReport(stock_class, stock_subclass, stock_number, stock_cars)


def register_stock_report_types(conn: Connection) -> None:
    register_type(conn, "TrainLegStockOutData", register_stock_report)


@dataclass
class ShortLegSegment:
    start: TrainStationIdentifiers
    end: TrainStationIdentifiers
    duration: timedelta
    mileage: Optional[Decimal]
    stocks: list[StockReport]


def register_short_leg_segment(
    segment_start: datetime,
    start_station: TrainStationIdentifiers,
    end_station: TrainStationIdentifiers,
    distance: Decimal,
    duration: timedelta,
    stock_data: list[StockReport],
) -> ShortLegSegment:
    return ShortLegSegment(
        start_station,
        end_station,
        duration,
        distance,
        stock_data,
    )


def register_short_leg_segment_types(conn: Connection) -> None:
    register_stock_report_types(conn)
    register_type(conn, "TrainLegStockOutData", register_short_leg_segment)


@dataclass
class ShortLegCall:
    station: TrainStationIdentifiers
    platform: Optional[str]
    plan_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_arr: Optional[datetime]
    act_dep: Optional[datetime]
    associated_service: Optional[list[ShortAssociatedService]]
    leg_stock: Optional[list[StockReport]]
    mileage: Optional[Decimal]


def register_leg_call_data(
    arr_call_id: int,
    arr_service_id: str,
    arr_service_run_date: datetime,
    plan_arr: datetime,
    act_arr: datetime,
    dep_call_id: int,
    dep_service_id: str,
    dep_service_run_date: datetime,
    plan_dep: datetime,
    act_dep: datetime,
    station: TrainStationIdentifiers,
    platform: str,
    mileage: Decimal,
    stocks: list[StockReport],
    assocs: list[ShortAssociatedService],
) -> ShortLegCall:
    return ShortLegCall(
        station,
        platform,
        change_timezone(plan_arr),
        change_timezone(plan_dep),
        change_timezone(act_arr),
        change_timezone(act_dep),
        assocs,
        stocks,
        mileage,
    )


def register_short_leg_call_types(conn: Connection) -> None:
    register_stock_report_types(conn)
    register_short_associated_service_types(conn)
    register_type(conn, "TrainLegCallOutData", register_leg_call_data)


@dataclass
class ShortLeg:
    id: int
    user_id: int
    leg_start: datetime
    services: dict[str, ShortTrainService]
    calls: list[ShortLegCall]
    stocks: list[ShortLegSegment]
    distance: Optional[Decimal]
    duration: Optional[timedelta]


def register_leg_data(
    leg_id: int,
    user_id: int,
    leg_start: datetime,
    leg_services: list[ShortTrainService],
    leg_calls: list[ShortLegCall],
    leg_stocks: list[ShortLegSegment],
    leg_distance: Decimal,
    leg_duration: timedelta,
) -> ShortLeg:
    leg_services_dict: dict[str, ShortTrainService] = {}
    for service in leg_services:
        leg_services_dict[service.service_id] = service
    return ShortLeg(
        leg_id,
        user_id,
        leg_start,
        leg_services_dict,
        leg_calls,
        leg_stocks,
        leg_distance,
        leg_duration,
    )


def register_leg_data_types(conn: Connection) -> None:
    register_short_train_service_types(conn)
    register_short_leg_call_types(conn)
    register_short_leg_segment_types(conn)
    register_type(conn, "TrainLegOutData", register_leg_data)

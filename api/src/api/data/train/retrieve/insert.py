from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from api.data.train.association import AssociatedType, string_of_associated_type
from api.user import User
from psycopg import Connection


@dataclass
class TrainServiceCallAssociatedServiceInData:
    associated_service: "TrainServiceInData"
    association: AssociatedType


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
    assoc_type: AssociatedType


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
    plan_dep: Optional[datetime]
    act_arr: Optional[datetime]
    act_dep: Optional[datetime]


@dataclass
class TrainLegCallInData:
    station_crs: str
    arr_call: Optional[TrainLegCallCallInData]
    dep_call: Optional[TrainLegCallCallInData]
    mileage: Optional[Decimal]
    assoc: Optional[AssociatedType]


@dataclass
class TrainStockReportCallInData:
    service_uid: str
    service_run_date: datetime
    station_crs: str
    plan: datetime
    act: datetime


@dataclass
class StockReport:
    class_no: Optional[int]
    subclass_no: Optional[int]
    stock_no: Optional[int]
    cars: Optional[int]


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


def insert_leg(conn: Connection, user: User, leg: TrainLegInData):
    service_data = []
    service_endpoint_data = []
    service_call_data = []
    service_association_data = []
    leg_call_data = []
    leg_stock_data = []
    for service in leg.services:
        service_data.append(
            (
                service.unique_identifier,
                service.run_date,
                service.headcode,
                service.operator_code,
                service.brand_code,
                service.power,
            )
        )
        for origin_name in service.origin_names:
            service_endpoint_data.append(
                (service.unique_identifier, service.run_date, origin_name, True)
            )
        for destination_name in service.destination_names:
            service_endpoint_data.append(
                (
                    service.unique_identifier,
                    service.run_date,
                    destination_name,
                    False,
                )
            )
        for call in service.calls:
            service_call_data.append(
                (
                    call.station_crs,
                    call.platform,
                    call.plan_arr,
                    call.act_arr,
                    call.plan_dep,
                    call.act_dep,
                    call.mileage,
                )
            )
            for association in call.associated_services:
                service_association_data.append(
                    (
                        association.associated_service.unique_identifier,
                        association.associated_service.run_date,
                        association.association,
                    )
                )
    for call in leg.calls:
        leg_call_data.append(
            (
                call.station_crs,
                (
                    call.arr_call.service_run_id
                    if call.arr_call is not None
                    else None
                ),
                call.arr_call.plan_arr if call.arr_call is not None else None,
                call.arr_call.act_arr if call.arr_call is not None else None,
                call.arr_call.plan_dep if call.arr_call is not None else None,
                call.arr_call.act_arr if call.arr_call is not None else None,
                call.dep_call.plan_arr if call.dep_call is not None else None,
                call.dep_call.act_arr if call.dep_call is not None else None,
                call.dep_call.plan_dep if call.dep_call is not None else None,
                call.dep_call.act_arr if call.dep_call is not None else None,
                call.mileage,
            )
        )
    for stock_report in leg.stock_reports:
        for stock in stock_report.stock_report:
            leg_stock_data.append(
                (
                    stock.class_no,
                    stock.subclass_no,
                    stock.stock_no,
                    stock.cars,
                    stock_report.start_call.service_uid,
                    stock_report.start_call.service_run_date,
                    stock_report.start_call.station_crs,
                    stock_report.start_call.plan,
                    stock_report.start_call.act,
                    stock_report.end_call.service_uid,
                    stock_report.end_call.service_run_date,
                    stock_report.end_call.station_crs,
                    stock_report.end_call.plan,
                    stock_report.end_call.act,
                )
            )
    leg_tuple = (
        user.user_id,
        service_data,
        service_endpoint_data,
        service_call_data,
        service_association_data,
        leg_call_data,
        leg.distance,
        leg_stock_data,
    )
    conn.execute(
        """
        SELECT * FROM InsertLeg(
            %s::TrainLegInData,
        )
        """,
        [leg_tuple],
    )
    conn.commit()

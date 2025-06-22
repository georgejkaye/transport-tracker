from datetime import datetime
from typing import Optional

from api.classes.train.stock import StockReport
from psycopg import Connection
from psycopg.rows import class_row

from api.classes.train.association import int_of_association_type
from api.classes.train.leg import (
    DbTrainLegCallInData,
    DbTrainLegInData,
    DbTrainStockSegmentInData,
    ShortLeg,
    TrainLegCallInData,
    TrainLegInData,
    TrainStockReportInData,
    register_leg_data_types,
)
from api.classes.train.service import (
    DbTrainAssociatedServiceInData,
    DbTrainCallInData,
    DbTrainServiceEndpointInData,
    DbTrainServiceInData,
    TrainServiceCallAssociatedServiceInData,
    TrainServiceCallInData,
    TrainServiceInData,
)
from api.classes.user import User


def get_db_service_tuple(
    service: TrainServiceInData,
) -> DbTrainServiceInData:
    return (
        service.unique_identifier,
        service.run_date,
        service.headcode,
        service.operator_code,
        service.brand_code,
        service.power,
    )


def get_db_service_endpoint_tuple(
    service: TrainServiceInData, name: str, is_origin: bool
) -> DbTrainServiceEndpointInData:
    return (service.unique_identifier, service.run_date, name, is_origin)


def get_db_service_call_tuple(
    service: TrainServiceInData, call: TrainServiceCallInData
) -> DbTrainCallInData:
    return (
        service.unique_identifier,
        service.run_date,
        call.station_crs,
        call.platform,
        call.plan_arr,
        call.act_arr,
        call.plan_dep,
        call.act_dep,
        call.mileage,
    )


def get_db_associated_service_tuple(
    service: TrainServiceInData,
    call: TrainServiceCallInData,
    association: TrainServiceCallAssociatedServiceInData,
) -> DbTrainAssociatedServiceInData:
    return (
        service.unique_identifier,
        service.run_date,
        call.station_crs,
        call.plan_arr,
        call.act_arr,
        call.plan_dep,
        call.act_dep,
        association.associated_service.unique_identifier,
        association.associated_service.run_date,
        int_of_association_type(association.association),
    )


def get_db_leg_call_tuple(leg_call: TrainLegCallInData) -> DbTrainLegCallInData:
    return (
        leg_call.station_crs,
        (
            leg_call.arr_call.service_run_id
            if leg_call.arr_call is not None
            else None
        ),
        (
            leg_call.arr_call.service_run_date
            if leg_call.arr_call is not None
            else None
        ),
        (leg_call.arr_call.plan_arr if leg_call.arr_call is not None else None),
        (leg_call.arr_call.act_arr if leg_call.arr_call is not None else None),
        (leg_call.arr_call.plan_dep if leg_call.arr_call is not None else None),
        (leg_call.arr_call.act_arr if leg_call.arr_call is not None else None),
        (
            leg_call.dep_call.service_run_id
            if leg_call.dep_call is not None
            else None
        ),
        (
            leg_call.dep_call.service_run_date
            if leg_call.dep_call is not None
            else None
        ),
        (leg_call.dep_call.plan_arr if leg_call.dep_call is not None else None),
        (leg_call.dep_call.act_arr if leg_call.dep_call is not None else None),
        (leg_call.dep_call.plan_dep if leg_call.dep_call is not None else None),
        (leg_call.dep_call.act_arr if leg_call.dep_call is not None else None),
        leg_call.mileage,
    )


def get_db_leg_stock_tuple(
    stock: StockReport, stock_report: TrainStockReportInData
) -> DbTrainStockSegmentInData:
    return (
        stock.class_no,
        stock.subclass_no,
        stock.stock_no,
        stock.cars,
        stock_report.start_call.service.unique_identifier,
        stock_report.start_call.service.run_date,
        stock_report.start_call.station_crs,
        (
            stock_report.start_call.dep_call.plan_dep
            if stock_report.start_call.dep_call is not None
            else None
        ),
        (
            stock_report.start_call.dep_call.act_dep
            if stock_report.start_call.dep_call is not None
            else None
        ),
        stock_report.end_call.service.unique_identifier,
        stock_report.end_call.service.run_date,
        stock_report.end_call.station_crs,
        (
            stock_report.end_call.arr_call.plan_arr
            if stock_report.end_call.arr_call is not None
            else None
        ),
        (
            stock_report.end_call.arr_call.act_arr
            if stock_report.end_call.arr_call is not None
            else None
        ),
    )


def insert_train_leg(conn: Connection, user: User, leg: TrainLegInData) -> None:
    service_data: list[DbTrainServiceInData] = []
    service_endpoint_data: list[DbTrainServiceEndpointInData] = []
    service_call_data: list[DbTrainCallInData] = []
    service_association_data: list[DbTrainAssociatedServiceInData] = []
    leg_call_data: list[DbTrainLegCallInData] = []
    leg_stock_data: list[DbTrainStockSegmentInData] = []
    services_to_add = [leg.primary_service] + [
        associated_service.associated_service
        for associated_service in leg.primary_service.associated_services
    ]
    for service in services_to_add:
        service_data.append(get_db_service_tuple(service))
        for origin_name in service.origin_names:
            service_endpoint_data.append(
                get_db_service_endpoint_tuple(service, origin_name, True)
            )
        for destination_name in service.destination_names:
            service_endpoint_data.append(
                get_db_service_endpoint_tuple(service, destination_name, False)
            )
        for call in service.calls:
            service_call_data.append(get_db_service_call_tuple(service, call))
            for association in call.associated_services:
                service_association_data.append(
                    get_db_associated_service_tuple(service, call, association)
                )
    for leg_call in leg.calls:
        leg_call_data.append(get_db_leg_call_tuple(leg_call))
    if leg.stock_reports is not None:
        for stock_report in leg.stock_reports:
            for stock in stock_report.stock_report:
                leg_stock_data.append(
                    get_db_leg_stock_tuple(stock, stock_report)
                )
    leg_tuple: DbTrainLegInData = (
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
        "SELECT * FROM insert_leg(%s::train_leg_in_data)",
        [leg_tuple],
    )
    conn.commit()


def select_legs(
    conn: Connection,
    user_id: int,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
    search_leg_id: Optional[int] = None,
) -> list[ShortLeg]:
    register_leg_data_types(conn)
    with conn.cursor(row_factory=class_row(ShortLeg)) as cur:
        rows = cur.execute(
            "SELECT SelectLegs(%s, %s, %s, %s)",
            [user_id, search_start, search_end, search_leg_id],
        ).fetchall()
        return rows

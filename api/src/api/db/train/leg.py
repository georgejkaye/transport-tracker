from datetime import datetime
from typing import Optional
from api.db.train.classes.output import ShortLeg, register_leg_data_types
from psycopg import Connection

from api.user import User
from api.db.train.classes.input import TrainLegInData


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


def select_legs(
    conn: Connection,
    user_id: int,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
    search_leg_id: Optional[int] = None,
) -> list[ShortLeg]:
    register_leg_data_types(conn)
    rows = conn.execute(
        "SELECT SelectLegs(%s, %s, %s, %s)",
        [user_id, search_start, search_end, search_leg_id],
    ).fetchall()

    return [row[0] for row in rows]

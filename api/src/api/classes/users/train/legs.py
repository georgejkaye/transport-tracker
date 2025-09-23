from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from psycopg import Connection

from api.utils.database import register_type


@dataclass
class DbTransportUserTrainLegStationOutData:
    station_id: int
    station_crs: str
    station_name: str


def register_transport_user_train_leg_station_out_data(
    conn: Connection,
) -> None:
    register_type(
        conn,
        "transport_user_train_leg_station_out_data",
        DbTransportUserTrainLegStationOutData,
    )


@dataclass
class DbTransportUserTrainLegOperatorOutData:
    operator_id: int
    operator_code: str
    operator_name: str


def register_transport_user_train_leg_operator_out_data(
    conn: Connection,
) -> None:
    register_type(
        conn,
        "transport_user_train_leg_operator_out_data",
        DbTransportUserTrainLegStationOutData,
    )


@dataclass
class DbTransportUserTrainLegOutData:
    leg_id: int
    origin: DbTransportUserTrainLegStationOutData
    destination: DbTransportUserTrainLegStationOutData
    start_datetime: datetime
    operator: DbTransportUserTrainLegOperatorOutData
    brand: DbTransportUserTrainLegOperatorOutData
    distance: Decimal
    duration: timedelta
    delay: int


def register_transport_user_train_leg_out_data(conn: Connection) -> None:
    register_type(
        conn,
        "transport_user_train_leg_out_data",
        DbTransportUserTrainLegOutData,
    )

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from api.utils.database import register_type
from psycopg import Connection


@dataclass
class DbTransportUserTrainLegStationOutData:
    id: int
    crs: str
    name: str


@dataclass
class DbTransportUserTrainLegOperatorOutData:
    id: int
    code: str
    name: str
    bg_colour: str
    fg_colour: str


@dataclass
class DbTransportUserTrainLegOutData:
    train_leg_id: int
    origin: DbTransportUserTrainLegStationOutData
    destination: DbTransportUserTrainLegStationOutData
    start_datetime: datetime
    operator: DbTransportUserTrainLegOperatorOutData
    brand: DbTransportUserTrainLegOperatorOutData
    distance: Decimal
    duration: timedelta
    delay: int


def register_db_transport_user_train_leg_out_data(conn: Connection) -> None:
    register_type(
        conn,
        "transport_user_train_leg_station_out_data",
        DbTransportUserTrainLegStationOutData,
    )
    register_type(
        conn,
        "transport_user_train_leg_operator_out_data",
        DbTransportUserTrainLegOperatorOutData,
    )
    register_type(
        conn,
        "transport_user_train_leg_out_data",
        DbTransportUserTrainLegOutData,
    )

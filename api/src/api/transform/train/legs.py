from datetime import datetime
from math import ceil
from typing import Optional

from psycopg import Connection

from api.api.pagination import Page
from api.db.functions.select.train.user.leg import (
    select_transport_user_train_legs_by_user_id_asc_fetchall,
    select_transport_user_train_legs_by_user_id_count_fetchone,
    select_transport_user_train_legs_by_user_id_desc_fetchall,
)
from api.db.types.user.train.leg import TransportUserTrainLegOutData


def get_user_train_leg_count_in_range(
    conn: Connection,
    user_id: int,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
) -> int:
    result = select_transport_user_train_legs_by_user_id_count_fetchone(
        conn, user_id, start_date, end_date
    )
    if result is None:
        raise RuntimeError("Could not get train leg count")
    return result.count


def get_user_train_legs_in_range(
    conn: Connection,
    user_id: int,
    page_size: int,
    page_no: int,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    descending: bool,
) -> Optional[Page[TransportUserTrainLegOutData]]:
    count = get_user_train_leg_count_in_range(
        conn, user_id, start_date, end_date
    )
    pages = ceil(count / page_size)
    if page_no >= pages:
        return None
    if descending:
        legs = select_transport_user_train_legs_by_user_id_desc_fetchall(
            conn,
            user_id,
            page_size,
            page_size * page_no,
            start_date,
            end_date,
        )
    else:
        legs = select_transport_user_train_legs_by_user_id_asc_fetchall(
            conn,
            user_id,
            page_size,
            page_size * page_no,
            start_date,
            end_date,
        )
    return Page(page_size, pages, page_no, legs)

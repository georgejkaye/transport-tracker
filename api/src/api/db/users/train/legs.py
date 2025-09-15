from datetime import datetime
from typing import Optional

from psycopg import Connection
from psycopg.rows import class_row

from api.classes.users.train.legs import DbTransportUserTrainLegOutData


def select_transport_user_train_leg_by_user_id(
    conn: Connection,
    user_id: int,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
) -> list[DbTransportUserTrainLegOutData]:
    with conn.cursor(
        row_factory=class_row(DbTransportUserTrainLegOutData)
    ) as cur:
        result = cur.execute(
            "SELECT * FROM select_transport_user_train_leg_by_user_id(%s, %s, %s)",
            [user_id, search_start, search_end],
        )
        return result.fetchall()

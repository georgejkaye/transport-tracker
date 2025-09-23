from datetime import datetime
from typing import Optional

from psycopg import Connection
from psycopg.rows import class_row

from api.classes.users.train.legs import DbTransportUserTrainLegOutData


def select_transport_user_train_leg_by_user_id(
    conn: Connection,
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[DbTransportUserTrainLegOutData]:
    with conn.cursor(
        row_factory=class_row(DbTransportUserTrainLegOutData)
    ) as cur:
        rows = cur.execute(
            "SELECT * FROM select_transport_user_train_leg_by_user_id(%s, %s, %s)",
            [user_id, start_date, end_date],
        ).fetchall()
        conn.commit()
        return rows

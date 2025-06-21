from datetime import datetime
from typing import Optional

from psycopg import Connection
from psycopg.rows import class_row

from api.classes.train.operators import BrandData


def select_operator_id(conn: Connection, operator_name: str) -> Optional[int]:
    with conn.cursor(row_factory=class_row(int)) as cur:
        rows = cur.execute(
            "SELECT * FROM select_operator_id_by_name(%s)", [operator_name]
        ).fetchall()
        if len(rows) != 1:
            return None
        row = rows[0]
        return row


def get_operator_brands(
    conn: Connection, operator_code: str, run_date: datetime
) -> list[BrandData]:
    with conn.cursor(row_factory=class_row(BrandData)) as cur:
        rows = cur.execute(
            "SELECT * FROM select_brands_by_operator_code(%s, %s)",
            [operator_code, run_date],
        ).fetchall()
        return rows

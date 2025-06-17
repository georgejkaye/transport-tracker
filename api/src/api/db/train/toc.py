from datetime import datetime
from typing import Optional

from psycopg import Connection
from psycopg.rows import class_row

from api.classes.train.operators import BrandData, register_brand_data_types


def select_operator_id(conn: Connection, operator_name: str) -> Optional[str]:
    statement = """
        SELECT operator_id
        FROM Operator
        WHERE operator_name = %(name)s
    """
    with conn.cursor(row_factory=class_row(str)) as cur:
        rows = cur.execute(statement, {"name": operator_name}).fetchall()
        if len(rows) != 1:
            return None
        row = rows[0]
        return row[0]


def get_operator_brands(
    conn: Connection, operator_code: str, run_date: datetime
) -> list[BrandData]:
    register_brand_data_types(conn)
    rows = conn.execute(
        "SELECT GetOperatorBrands(%s, %s)", [operator_code, run_date]
    ).fetchall()
    return [row[0] for row in rows]

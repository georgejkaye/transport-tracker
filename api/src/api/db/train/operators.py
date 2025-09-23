from datetime import datetime
from typing import Optional

from psycopg import Connection
from psycopg.rows import class_row

from api.classes.train.operators import (
    BrandData,
    DbTrainOperatorDetailsOutData,
    DbTrainOperatorOutData,
    OperatorBrandLookup,
    OperatorData,
    operator_db_data_to_operator_data,
)


def select_operator_id(conn: Connection, operator_name: str) -> Optional[int]:
    with conn.cursor(row_factory=class_row(int)) as cur:
        row = cur.execute(
            "SELECT * FROM select_operator_id_by_name(%s)", [operator_name]
        ).fetchone()
        conn.commit()
        return row if not None else None


def get_operator_brands(
    conn: Connection, operator_code: str, run_date: datetime
) -> list[BrandData]:
    with conn.cursor(row_factory=class_row(BrandData)) as cur:
        rows = cur.execute(
            "SELECT * FROM select_brands_by_operator_code(%s, %s)",
            [operator_code, run_date],
        ).fetchall()
        conn.commit()
        return rows


def get_operator_by_operator_by_operator_code(
    conn: Connection, operator_code: str, run_date: datetime
) -> Optional[OperatorData]:
    with conn.cursor(row_factory=class_row(DbTrainOperatorOutData)) as cur:
        row = cur.execute(
            "SELECT * FROM select_operator_by_operator_code(%s, %s)",
            [operator_code, run_date],
        ).fetchone()
        conn.commit()
        return (
            operator_db_data_to_operator_data(row) if row is not None else None
        )


def select_operator_details(conn: Connection) -> OperatorBrandLookup:
    with conn.cursor(
        row_factory=class_row(DbTrainOperatorDetailsOutData)
    ) as cur:
        rows = cur.execute("SELECT * FROM select_operator_details()").fetchall()
        conn.commit()
        operators: dict[int, DbTrainOperatorDetailsOutData] = {}
        brands: dict[int, DbTrainOperatorDetailsOutData] = {}
        for row in rows:
            if row.is_brand:
                brands[row.operator_id] = row
            else:
                operators[row.operator_id] = row
        return OperatorBrandLookup(operators, brands)

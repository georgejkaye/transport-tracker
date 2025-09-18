from datetime import datetime
from typing import Optional

from psycopg import Connection
from psycopg.rows import class_row

from api.classes.train.operators import (
    BrandData,
    DbOperatorDetails,
    OperatorBrandLookup,
    OperatorData,
    OperatorDbData,
    operator_db_data_to_operator_data,
)
from api.utils.database import register_type


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


def get_operator_by_operator_by_operator_code(
    conn: Connection, operator_code: str, run_date: datetime
) -> Optional[OperatorData]:
    register_train_operator_out_data(conn)
    with conn.cursor(row_factory=class_row(OperatorDbData)) as cur:
        row = cur.execute(
            "SELECT * FROM select_operator_by_operator_code(%s, %s)",
            [operator_code, run_date],
        ).fetchone()
        return (
            operator_db_data_to_operator_data(row) if row is not None else None
        )


def register_train_operator_out_data(conn: Connection) -> None:
    register_type(conn, "train_brand_out_data", BrandData)


def select_operator_details(conn: Connection) -> OperatorBrandLookup:
    with conn.cursor(row_factory=class_row(DbOperatorDetails)) as cur:
        rows = cur.execute("SELECT * FROM select_operator_details()").fetchall()
        operators: dict[int, DbOperatorDetails] = {}
        brands: dict[int, DbOperatorDetails] = {}
        for row in rows:
            if row.is_brand:
                brands[row.operator_id] = row
            else:
                operators[row.operator_id] = row
        return OperatorBrandLookup(operators, brands)

from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from psycopg import Connection
from psycopg.rows import class_row

from api.utils.database import register_type


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


@dataclass
class OperatorData:
    id: int
    code: str
    name: str
    bg: Optional[str]
    fg: Optional[str]


@dataclass
class BrandData:
    id: int
    code: str
    name: str
    bg: Optional[str]
    fg: Optional[str]


def register_brand_data(
    brand_id: int,
    brand_code: str,
    brand_name: str,
    brand_bg: str,
    brand_fg: str,
) -> BrandData:
    return BrandData(brand_id, brand_code, brand_name, brand_bg, brand_fg)


def register_brand_data_types(conn: Connection) -> None:
    register_type(conn, "OutBrandData", register_brand_data)


def get_operator_brands(
    conn: Connection, operator_code: str, run_date: datetime
) -> list[BrandData]:
    register_brand_data_types(conn)
    rows = conn.execute(
        "SELECT GetOperatorBrands(%s, %s)", [operator_code, run_date]
    ).fetchall()
    return [row[0] for row in rows]

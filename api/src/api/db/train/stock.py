from datetime import datetime

from api.utils.database import register_type
from psycopg import Connection
from psycopg.rows import class_row

from api.classes.train.stock import (
    Class,
    ClassAndSubclass,
    Stock,
    StockSubclass,
)


def get_unique_classes_from_subclasses(
    stock: list[ClassAndSubclass],
) -> list[Class]:
    uniques: set[Class] = set()
    for cas in stock:
        current_class = Class(cas.class_no, cas.class_name)
        if current_class not in uniques:
            uniques.add(current_class)
    return list(uniques)


def get_operator_stock(
    conn: Connection, operator_code: str, run_date: datetime
) -> list[Stock]:
    register_type(conn, "train_stock_subclass_out_data", StockSubclass)
    with conn.cursor(row_factory=class_row(Stock)) as cur:
        rows = cur.execute(
            "SELECT * FROM select_operator_stock(%s, %s)",
            [operator_code, run_date],
        ).fetchall()
        return rows


def get_unique_classes(stock: list[Stock]) -> list[Class]:
    stock_classes: set[Class] = set()
    for item in stock:
        stock_class = Class(item.stock_class, item.stock_class_name)
        stock_classes.add(stock_class)
    return list(stock_classes)

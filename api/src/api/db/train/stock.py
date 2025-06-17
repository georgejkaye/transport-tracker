from datetime import datetime
from typing import Optional

from psycopg import Connection

from api.classes.train.stock import Class, ClassAndSubclass, Formation, Stock


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
    query = """
        SELECT
            Stock.stock_class, Stock.name AS stock_name,
            StockSubclass.stock_subclass, StockSubclass.name AS stock_subclass,
            OperatorStock.operator_id, OperatorStock.brand_id
        FROM Stock
        LEFT JOIN StockSubclass
        ON Stock.stock_class = StockSubclass.stock_class
        INNER JOIN OperatorStock
        ON
            Stock.stock_class = OperatorStock.stock_class AND (
                StockSubclass.stock_subclass IS NULL
                OR
                StockSubclass.stock_subclass = OperatorStock.stock_subclass
            )
        INNER JOIN Operator
        ON OperatorStock.operator_id = Operator.operator_id
        LEFT JOIN Brand
        ON OperatorStock.brand_id = Brand.brand_id
        WHERE
            (operator_code = %(code)s OR brand_code = %(code)s)
        AND
            %(rundate)s <@ operation_range
        ORDER BY Stock.stock_class ASC, StockSubclass.stock_subclass ASC
    """
    rows = conn.execute(
        query, {"code": operator_code, "rundate": run_date.date()}
    ).fetchall()
    stock = [
        Stock(row[0], row[1], row[2], row[3], row[4], row[5]) for row in rows
    ]
    return stock


def get_unique_classes(stock: list[Stock]) -> list[Class]:
    stock_classes: set[Class] = set()
    for item in stock:
        stock_class = Class(item.class_no, item.class_name)
        stock_classes.add(stock_class)
    return list(stock_classes)


def get_unique_subclasses(
    stock: list[Stock], stock_class: Optional[Class] = None
) -> list[ClassAndSubclass]:
    stock_subclasses: set[ClassAndSubclass] = set()
    for item in stock:
        if stock_class and item.class_no == stock_class.class_no:
            if item.subclass_no is not None:
                stock_subclass = ClassAndSubclass(
                    item.class_no,
                    item.class_name,
                    item.subclass_no,
                    item.class_name,
                )
                stock_subclasses.add(stock_subclass)
    return list(stock_subclasses)


def select_stock_cars(
    conn: Connection, stock: Stock, run_date: datetime
) -> list[Formation]:
    rows = conn.execute(
        "SELECT GetStockCars(%s, %s, %s, %s, %s)",
        [
            stock.class_no,
            stock.subclass_no,
            stock.operator,
            stock.brand,
            run_date,
        ],
    ).fetchall()
    car_list = [Formation(row[0]) for row in rows]
    return car_list

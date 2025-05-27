from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from psycopg import Connection


@dataclass
class Class:
    class_no: int
    class_name: Optional[str]

    def __hash__(self):
        return hash(self.class_no)


def string_of_class(stock_class: Class) -> str:
    string = f"Class {stock_class.class_no}"
    if stock_class.class_name is not None:
        string = f"{string} ({stock_class.class_name})"
    return string


def sort_by_classes(stock: list[Class]) -> list[Class]:
    return sorted(stock, key=lambda x: x.class_no)


@dataclass
class ClassAndSubclass:
    class_no: int
    class_name: Optional[str]
    subclass_no: Optional[int]
    subclass_name: Optional[str]

    def __hash__(self):
        if self.subclass_no is None:
            subclass_hash = 0
        else:
            subclass_hash = self.subclass_no
        return hash(self.class_no * 10 + subclass_hash)


def string_of_class_and_subclass(
    stock: ClassAndSubclass, name: bool = True
) -> str:
    string = f"Class {stock.class_no}"
    if stock.subclass_no is not None:
        string = f"{string}/{stock.subclass_no}"
    if name:
        if stock.subclass_name is not None:
            string = f"{string} ({stock.subclass_name})"
        elif stock.class_name is not None:
            string = f"{string} ({stock.class_name})"
    return string


def subclass_sort_key(stock: ClassAndSubclass) -> int:
    if stock.subclass_no is None:
        return stock.class_no * 10
    else:
        return stock.class_no * 10 + stock.subclass_no


def sort_by_subclasses(stock: list[ClassAndSubclass]) -> list[ClassAndSubclass]:
    return sorted(stock, key=subclass_sort_key)


def get_unique_classes_from_subclasses(
    stock: list[ClassAndSubclass],
) -> list[Class]:
    uniques: set[Class] = set()
    for cas in stock:
        if cas.class_no not in uniques:
            current_class = Class(cas.class_no, cas.class_name)
            uniques.add(current_class)
    return list(uniques)


@dataclass
class StockUnit:
    class_no: int
    class_name: Optional[str]
    subclass_no: int
    subclass_name: Optional[str]
    unit_no: int


@dataclass
class Stock:
    class_no: int
    class_name: Optional[str]
    subclass_no: Optional[int]
    subclass_name: Optional[str]
    operator: str
    brand: Optional[str]


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
    stock_classes = set()
    for item in stock:
        stock_class = Class(item.class_no, item.class_name)
        stock_classes.add(stock_class)
    return list(stock_classes)


def get_unique_subclasses(
    stock: list[Stock], stock_class: Optional[Class] = None
) -> list[ClassAndSubclass]:
    stock_subclasses = set()
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


@dataclass
class Formation:
    cars: int


def string_of_formation(f: Formation) -> str:
    return f"{f.cars} cars"


def select_stock_cars(
    conn: Connection, stock: Stock, run_date: datetime
) -> list[Formation]:
    statement = """
        SELECT DISTINCT cars FROM StockFormation
        INNER JOIN (
            SELECT Stock.stock_class, StockSubclass.stock_subclass
            FROM stock
            LEFT JOIN StockSubclass
            ON Stock.stock_class = StockSubclass.stock_class
        ) Stocks
        ON StockFormation.stock_class = Stocks.stock_class
        AND (
            (Stocks.stock_subclass = StockFormation.stock_subclass)
            OR (
                Stocks.stock_subclass IS NULL
                AND StockFormation.stock_subclass IS NULL
            )
        )
        INNER JOIN OperatorStock
        ON Stocks.stock_class = OperatorStock.stock_class
        AND (
            (Stocks.stock_subclass = OperatorStock.stock_subclass)
            OR (
                Stocks.stock_subclass IS NULL
                AND OperatorStock.stock_subclass IS NULL
            )
        )
        INNER JOIN Operator
        ON OperatorStock.operator_id = Operator.operator_id
        WHERE Stocks.stock_class = %(class_no)s
        AND operator_code = %(operator)s
        AND %(rundate)s <@ operation_range
    """
    if stock.subclass_no is not None:
        statement = f"""
            {statement} AND Stocks.stock_subclass = %(subclass_no)s
        """
    if stock.brand is not None:
        statement = f"""
            {statement} AND brand_code = %(brand)s
        """
    statement = f"{statement} ORDER BY cars ASC"
    rows = conn.execute(
        statement,
        {
            "class_no": stock.class_no,
            "operator": stock.operator,
            "subclass_no": stock.subclass_no,
            "brand": stock.brand,
            "rundate": run_date.date(),
        },
    ).fetchall()
    car_list = [Formation(row[0]) for row in rows]
    return car_list

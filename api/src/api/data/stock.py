from typing import Optional

from dataclasses import dataclass
from api.data.database import NoEscape, connect, insert
from api.data.toc import Toc, TocWithBrand, get_tocs
from psycopg2._psycopg import connection, cursor


def display_tocs(tocs: list[TocWithBrand]):
    i = 1
    for toc in tocs:
        print(f"{i}: {toc.name}")
        i = i + 1


def display_brands(brands: list[Toc]):
    i = 1
    for brand in brands:
        print(f"{i}: {brand.name}")
        i = i + 1


def get_number(prompt: str, max: Optional[int] = None):
    entry = input(f"{prompt}: ")
    if not entry.isnumeric():
        return None
    number = int(entry)
    if max is not None and number > max:
        return None
    return number


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


def string_of_class_and_subclass(stock: ClassAndSubclass, name: bool = True) -> str:
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


def get_unique_classes_from_subclasses(stock: list[ClassAndSubclass]) -> list[Class]:
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


def string_of_stock(stock: Stock) -> str:
    string = f"Class {stock.class_no}"
    if stock.subclass_no is not None:
        string = f"{string}/{stock.subclass_no}"
    if stock.subclass_name is not None:
        string = f"{string} ({stock.subclass_name})"
    elif stock.class_name is not None:
        string = f"{string} ({stock.class_name})"
    return string


def stock_to_values(stock: Stock) -> list[str | None | NoEscape]:
    elem_0 = str(stock.class_no)
    if stock.subclass_no is None:
        elem_1 = None
    else:
        elem_1 = str(stock.subclass_no)
    if stock.subclass_name is None:
        elem_2 = None
    else:
        elem_2 = str(stock.subclass_name)
    return [elem_0, elem_1, elem_2]


def stock_to_current(stock: Stock) -> list[str | None | NoEscape]:
    elem_0 = stock.operator
    if stock.brand is None:
        elem_1 = None
    else:
        elem_1 = stock.brand
    elem_2 = str(stock.class_no)
    if stock.subclass_no is None:
        elem_3 = None
    else:
        elem_3 = str(stock.subclass_no)
    return [elem_0, elem_1, elem_2, elem_3]


def insert_stock(conn: connection, cur: cursor, stocks: list[Stock]):
    stock_fields = ["stock_class", "subclass", "name"]
    stock_values = [stock_to_values(stock) for stock in stocks]
    insert(cur, "Stock", stock_fields, stock_values, "ON CONFLICT DO NOTHING")
    current_fields = ["operator_id", "brand_id", "stock_class", "subclass"]
    current_values = [stock_to_current(stock) for stock in stocks]
    insert(
        cur, "OperatorStock", current_fields, current_values, "ON CONFLICT DO NOTHING"
    )


def insert_stock_interactive():
    (conn, cur) = connect()
    tocs = get_tocs(conn, cur)
    ready = True
    while ready:
        display_tocs(tocs)
        operator_index = get_number("Select operator", len(tocs))
        if operator_index is not None:
            operator = tocs[operator_index - 1]
            if len(operator.brand) > 0:
                display_brands(operator.brand)
                brand_index = get_number("Select brand", len(operator.brand))
                if brand_index is not None:
                    brand = operator.brand[brand_index - 1]
                else:
                    brand = None
            else:
                brand = None
            stock = ""
            while stock is not None:
                class_no = input("Class no: ")
                class_name = input("Class name: ")
                if class_name == "":
                    class_name_option = None
                else:
                    class_name_option = class_name
                subclass_no = input("Subclass no: ")
                if subclass_no == "":
                    subclass = None
                else:
                    subclass = int(subclass_no)
                subclass_name = input("Subclass name: ")
                if subclass_name == "":
                    subclass_name_option = None
                else:
                    subclass_name_option = subclass_name
                if brand is None:
                    brand_id = None
                else:
                    brand_id = brand.atoc
                stock = Stock(
                    int(class_no),
                    class_name_option,
                    subclass,
                    subclass_name_option,
                    operator.atoc,
                    brand_id,
                )
                insert_stock(conn, cur, [stock])
                conn.commit()

        else:
            exit(1)


def get_operator_stock(cur: cursor, operator: str) -> list[Stock]:
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
            Stock.stock_class = OperatorStock.stock_class AND
            (StockSubclass.stock_subclass IS NULL OR StockSubclass.stock_subclass = OperatorStock.stock_subclass)
        WHERE
            OperatorStock.operator_id = %(id)s OR OperatorStock.brand_id = %(id)s
        ORDER BY Stock.stock_class ASC, StockSubclass.stock_subclass ASC
    """
    cur.execute(query, {"id": operator})
    rows = cur.fetchall()
    stock = [Stock(row[0], row[1], row[2], row[3], row[4], row[5]) for row in rows]
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
                    item.class_no, item.class_name, item.subclass_no, item.class_name
                )
                stock_subclasses.add(stock_subclass)
    return list(stock_subclasses)


@dataclass
class Formation:
    cars: int


def string_of_formation(f: Formation) -> str:
    return f"{f.cars} cars"


def select_stock_cars(cur: cursor, stock: Stock) -> list[Formation]:
    statement = """
        SELECT DISTINCT cars FROM StockFormation
        INNER JOIN (
            SELECT Stock.stock_class, StockSubclass.stock_subclass
            FROM stock
            LEFT JOIN StockSubclass
            ON Stock.stock_class = StockSubclass.stock_class
        ) Stocks
        ON StockFormation.stock_class = Stocks.stock_class
        AND StockFormation.stock_subclass = Stocks.stock_subclass
        INNER JOIN OperatorStock
        ON Stocks.stock_class = OperatorStock.stock_class
        AND Stocks.stock_subclass = OperatorStock.stock_subclass
        WHERE Stocks.stock_class = %(class_no)s
        AND operator_id = %(operator)s
    """
    if stock.subclass_no is not None:
        statement = f"""
            {statement} AND Stocks.stock_subclass = %(subclass_no)s
        """
    if stock.brand is not None:
        statement = f"""
            {statement} AND brand_id = %(brand)s
        """
    statement = f"{statement} ORDER BY cars ASC"
    cur.execute(
        statement,
        {
            "class_no": stock.class_no,
            "operator": stock.operator,
            "subclass_no": stock.subclass_no,
            "brand": stock.brand,
        },
    )
    rows = cur.fetchall()
    car_list = [Formation(row[0]) for row in rows]
    return car_list


if __name__ == "__main__":
    insert_stock_interactive()

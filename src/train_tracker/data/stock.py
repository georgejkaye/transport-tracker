from typing import Optional

from dataclasses import dataclass
from train_tracker.data.database import connect, insert
from train_tracker.data.toc import Toc, TocWithBrand, get_tocs
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


def stock_to_values(stock: Stock) -> list[str | None]:
    elem_0 = str(stock.class_no)
    if stock.subclass_no is None:
        elem_1 = None
    else:
        elem_1 = str(stock.subclass_no)
    if stock.name is None:
        elem_2 = None
    else:
        elem_2 = str(stock.name)
    return [elem_0, elem_1, elem_2]


def stock_to_current(stock: Stock) -> list[str | None]:
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
                subclass_no = input("Subclass no: ")
                if subclass_no == "":
                    subclass = None
                else:
                    subclass = int(subclass_no)
                stock_name = input("Stock name: ")
                if stock_name == "":
                    stock_namee = None
                else:
                    stock_namee = stock_name
                if brand is None:
                    brand_id = None
                else:
                    brand_id = brand.atoc
                stock = Stock(
                    int(class_no), subclass, stock_namee, operator.atoc, brand_id
                )
                insert_stock(conn, cur, [stock])
                conn.commit()

        else:
            exit(1)


def get_operator_stock(cur: cursor, operator: str) -> list[Stock]:
    query = """
        SELECT
            Stock.stock_class, Stock.name,
            StockSubclass.stock_subclass, StockSubclass.name,
            OperatorStock.operator_id, OperatorStock.brand_id
        FROM Stock
        LEFT JOIN StockSubclass
        ON Stock.stock_class = StockSubclass.stock_class
        INNER JOIN OperatorStock
        ON
            Stock.stock_class = OperatorStock.stock_class AND
            StockSubclass.stock_subclass = OperatorStock.stock_subclass
        WHERE
            OperatorStock.operator_id = %(id)s OR OperatorStock.brand_id = %(id)s
    """
    cur.execute(query, {"id": operator})
    rows = cur.fetchall()
    stock = [Stock(row[0], row[1], row[2], row[3], row[4], row[5]) for row in rows]
    return stock


if __name__ == "__main__":
    insert_stock_interactive()

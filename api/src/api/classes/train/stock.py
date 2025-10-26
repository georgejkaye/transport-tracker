from dataclasses import dataclass
from typing import Optional

from api.db.types.train.stock import TrainStockOutData


@dataclass
class Class:
    class_no: int
    class_name: Optional[str]

    def __hash__(self) -> int:
        return hash(self.class_no)


@dataclass
class ClassAndSubclass:
    class_no: int
    class_name: Optional[str]
    subclass_no: Optional[int]
    subclass_name: Optional[str]

    def __hash__(self) -> int:
        if self.subclass_no is None:
            subclass_hash = 0
        else:
            subclass_hash = self.subclass_no
        return hash(self.class_no * 10 + subclass_hash)


@dataclass
class StockUnit:
    class_no: int
    class_name: Optional[str]
    subclass_no: int
    subclass_name: Optional[str]
    unit_no: int


@dataclass
class StockSubclass:
    stock_subclass: Optional[int]
    stock_subclass_name: Optional[str]
    stock_cars: list[int]


def sort_by_subclasses(stock: list[StockSubclass]) -> list[StockSubclass]:
    return sorted(
        stock,
        key=lambda c: c.stock_subclass if c.stock_subclass is not None else -1,
    )


@dataclass
class Stock:
    stock_class: int
    stock_class_name: Optional[str]
    stock_subclasses: list[StockSubclass]


def string_of_class(stock_class: TrainStockOutData) -> str:
    string = f"Class {stock_class.stock_class}"
    if stock_class.stock_class_name is not None:
        string = f"{string} ({stock_class.stock_class_name})"
    return string


def string_of_class_and_subclass(
    stock: Stock, subclass: StockSubclass, name: bool = True
) -> str:
    string = f"Class {stock.stock_class}"
    if subclass.stock_subclass is not None:
        string = f"{string}/{subclass.stock_subclass}"
    if name:
        if subclass.stock_subclass_name is not None:
            string = f"{string} ({subclass.stock_subclass_name})"
        elif stock.stock_class_name is not None:
            string = f"{string} ({stock.stock_class_name})"
    return string


def sort_by_classes(stock: list[TrainStockOutData]) -> list[TrainStockOutData]:
    return sorted(stock, key=lambda x: x.stock_class)


@dataclass
class Formation:
    cars: int


def string_of_formation(f: Formation) -> str:
    return f"{f.cars} cars"


@dataclass
class StockReport:
    class_no: Optional[int]
    subclass_no: Optional[int]
    stock_no: Optional[int]
    cars: Optional[int]


def string_of_stock_report(report: StockReport) -> str:
    if report.class_no is None:
        return "Unknown"
    if report.stock_no is not None:
        return str(report.stock_no)
    if report.subclass_no is None:
        return f"Class {report.class_no}"
    return f"Class {report.class_no}/{report.subclass_no}"

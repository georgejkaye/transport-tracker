from dataclasses import dataclass
from typing import Optional

from api.db.types.train.leg import TrainLegStockSegmentReportInData
from api.db.types.train.stock import (
    TrainStockOutData,
    TrainStockSubclassOutData,
)


def sort_by_subclasses(
    stock: list[TrainStockSubclassOutData],
) -> list[TrainStockSubclassOutData]:
    return sorted(
        stock,
        key=lambda c: c.stock_subclass if c.stock_subclass is not None else -1,
    )


def string_of_class(stock_class: TrainStockOutData) -> str:
    string = f"Class {stock_class.stock_class}"
    if stock_class.stock_class_name is not None:
        string = f"{string} ({stock_class.stock_class_name})"
    return string


def string_of_class_and_subclass(
    stock: TrainStockOutData,
    subclass: TrainStockSubclassOutData,
    name: bool = True,
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


def string_of_stock_report(report: TrainLegStockSegmentReportInData) -> str:
    if report.stock_class is None:
        return "Unknown"
    if report.stock_number is not None:
        return str(report.stock_number)
    if report.stock_subclass is None:
        return f"Class {report.stock_class}"
    return f"Class {report.stock_class}/{report.stock_subclass}"

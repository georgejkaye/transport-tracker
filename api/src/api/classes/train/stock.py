from dataclasses import dataclass
from typing import Optional


@dataclass
class Class:
    class_no: int
    class_name: Optional[str]

    def __hash__(self) -> int:
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

    def __hash__(self) -> int:
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

from typing import Optional

from api.db.types.train.stock import (
    TrainStockOutData,
    TrainStockSubclassOutData,
)
from api.record.classes import StockReport, StockSegment
from api.utils.interactive.classes import PickMultiple, PickSingle, PickUnknown
from api.utils.interactive.input import (
    get_choice_from_input,
    get_choices_from_input,
    get_int_from_input,
    print_information,
)


def get_next_segment_stock(
    stock_list: list[TrainStockOutData],
    previous_stock_segment: Optional[StockSegment],
) -> list[StockReport]:
    previous_stock = _get_stock_from_previous_stock_segment(
        previous_stock_segment
    )
    remaining_stock = _get_remaining_stock_from_previous_stock_segment(
        previous_stock
    )
    new_stock = _get_new_stock(stock_list)
    return remaining_stock + new_stock


def _get_stock_from_previous_stock_segment(
    previous_stock_segment: Optional[StockSegment],
) -> list[StockReport]:
    return (
        previous_stock_segment.stock_reports
        if previous_stock_segment is not None
        else []
    )


def _get_remaining_stock_from_previous_stock_segment(
    previous_stock: list[StockReport],
) -> list[StockReport]:
    if len(previous_stock) == 0:
        return []
    result = get_choices_from_input(
        "Which units remain",
        previous_stock,
        _string_of_stock_report,
    )
    match result:
        case None:
            return []
        case PickMultiple(choices):
            return choices


def _string_of_stock_report(report: StockReport) -> str:
    if report.class_no is None:
        return "Unknown"
    if report.subclass_no is not None:
        return str(report.stock_no)
    if report.subclass_no is None:
        return f"Class {report.class_no}"
    return f"Class {report.class_no}/{report.subclass_no}"


def _get_new_stock(stock_list: list[TrainStockOutData]) -> list[StockReport]:
    number_of_units = get_int_from_input("Number of new units")
    if number_of_units is None:
        return []
    new_stock: list[StockReport] = []
    for i in range(0, number_of_units):
        print_information(f"Selecting unit {i + 1}")
        stock_report = _get_unit_report_from_input(stock_list)
        if stock_report is None:
            return []
        new_stock.append(stock_report)
    return new_stock


def _get_unit_class_from_input(
    operator_stock: list[TrainStockOutData],
) -> Optional[PickUnknown | PickSingle[TrainStockOutData]]:
    chosen_class = get_choice_from_input(
        "Class number",
        _sort_by_classes(operator_stock),
        unknown=True,
        display=_string_of_class,
    )
    match chosen_class:
        case None:
            return None
        case PickUnknown():
            return chosen_class
        case PickSingle(_):
            return chosen_class
        case _:
            return None


def _get_unit_subclass_from_input(
    stock: TrainStockOutData,
) -> Optional[PickUnknown | PickSingle[TrainStockSubclassOutData]]:
    if len(stock.stock_subclasses) == 1:
        return PickSingle(stock.stock_subclasses[0])
    else:
        chosen_subclass = get_choice_from_input(
            "Subclass no",
            _sort_by_subclasses(stock.stock_subclasses),
            unknown=True,
            cancel=False,
            display=lambda c: _string_of_class_and_subclass(stock, c),
        )
        match chosen_subclass:
            case None:
                return None
            case PickUnknown():
                return chosen_subclass
            case PickSingle(_):
                return chosen_subclass
            case _:
                return None


def _get_unit_no_from_input(
    stock_class: TrainStockOutData,
) -> Optional[int]:
    while True:
        unit_no_opt = get_int_from_input(
            "Stock number",
            lower=stock_class.stock_class * 1000,
            upper=stock_class.stock_class * 1000 + 999,
            unknown=True,
        )
        return unit_no_opt


def _get_unit_cars_from_input(
    stock_class: TrainStockOutData,
    stock_subclass: TrainStockSubclassOutData,
) -> PickUnknown | PickSingle[int] | None:
    if len(stock_subclass.stock_cars) == 1:
        print_information(
            f"{_string_of_class_and_subclass(stock_class, stock_subclass, name=False)} always has {stock_subclass.stock_cars[0]} cars"
        )
        return PickSingle(stock_subclass.stock_cars[0])
    result = get_choice_from_input(
        "Number of cars",
        stock_subclass.stock_cars,
        lambda c: f"{c} car{'s' if c > 1 else ''}",
        unknown=True,
    )
    match result:
        case None:
            return None
        case PickUnknown():
            return result
        case PickSingle(_):
            return result
        case _:
            return None


def _sort_by_classes(
    stock: list[TrainStockOutData],
) -> list[TrainStockOutData]:
    return sorted(stock, key=lambda x: x.stock_class)


def _sort_by_subclasses(
    stock: list[TrainStockSubclassOutData],
) -> list[TrainStockSubclassOutData]:
    return sorted(
        stock,
        key=lambda c: (
            c.stock_subclass if c.stock_subclass is not None else -1
        ),
    )


def _string_of_class(stock_class: TrainStockOutData) -> str:
    string = f"Class {stock_class.stock_class}"
    if stock_class.stock_class_name is not None:
        string = f"{string} ({stock_class.stock_class_name})"
    return string


def _string_of_class_and_subclass(
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


def _get_unit_report_from_input(
    stock_list: list[TrainStockOutData],
) -> Optional[StockReport]:
    stock_class_input = _get_unit_class_from_input(stock_list)
    stock_data = _get_stock_data(stock_class_input)
    stock_subclass_data = _get_stock_subclass_data(stock_data)
    stock_unit_no = _get_stock_no(stock_data, stock_subclass_data)
    stock_cars = _get_stock_cars(stock_data, stock_subclass_data)
    return StockReport(
        stock_data.stock_class if stock_data is not None else None,
        (
            stock_subclass_data.stock_subclass
            if stock_subclass_data is not None
            else None
        ),
        stock_unit_no,
        stock_cars,
    )


def _get_stock_data(
    stock_class_input: Optional[PickUnknown | PickSingle[TrainStockOutData]],
) -> Optional[TrainStockOutData]:
    match stock_class_input:
        case PickSingle(stock_class_choice):
            return stock_class_choice
        case _:
            return None


def _get_stock_subclass_data(
    stock_data: Optional[TrainStockOutData],
) -> Optional[TrainStockSubclassOutData]:
    if stock_data is not None:
        stock_subclass_input = _get_unit_subclass_from_input(stock_data)
        match stock_subclass_input:
            case PickSingle(stock_subclass_choice):
                return stock_subclass_choice
            case _:
                return None
    else:
        return None


def _get_stock_no(
    stock_data: Optional[TrainStockOutData],
    stock_subclass_data: Optional[TrainStockSubclassOutData],
) -> Optional[int]:
    if stock_data is not None and stock_subclass_data is not None:
        return _get_unit_no_from_input(stock_data)
    return None


def _get_stock_cars(
    stock_data: Optional[TrainStockOutData],
    stock_subclass_data: Optional[TrainStockSubclassOutData],
) -> Optional[int]:
    if stock_data is not None and stock_subclass_data is not None:
        stock_cars_input = _get_unit_cars_from_input(
            stock_data, stock_subclass_data
        )
        match stock_cars_input:
            case PickSingle(form):
                return form
            case _:
                return None
    return None

from dataclasses import dataclass
from datetime import datetime
from math import ceil
from typing import Callable, Optional
from questionary import Choice, checkbox, text
from termcolor import colored

from api.utils.times import make_timezone_aware
from api.library.questionary import (
    ask_bool_question,
    ask_select_question,
    ask_text_question,
)


def thick_line(length: int = 80) -> None:
    print("=" * length)


def thin_line(length: int = 80) -> None:
    print("-" * length)


def space() -> None:
    print()


def message(msg: str) -> None:
    print(msg)


def option(number: int, choice: str) -> None:
    print(f"{number}: {choice}")


def header(msg: str, length: int = 80) -> None:
    thick_line(length)
    message(msg)
    thick_line(length)
    space()


def subheader(msg: str, length: int = 80) -> None:
    thin_line(length)
    message(msg)
    thin_line(length)
    space()


def information(msg: str, end: str | None = None) -> None:
    exclamation = colored("!", "dark_grey")
    message = colored(msg, attrs=["bold"])
    print(f"{exclamation} {message}", end=end)


def input_text(message: str, default: str = "") -> Optional[str]:
    return ask_text_question(message=message, default=default)


def number_in_range(
    input: str,
    lower: Optional[int],
    upper: Optional[int],
    unknown: bool = False,
) -> bool | str:
    if unknown and input == "":
        return True
    if not input.isnumeric():
        return f"Expected a number but got '{input}'"
    input_number = int(input)
    if (lower is not None and input_number < lower) or (
        upper is not None and input_number > upper
    ):
        return f"Expected number in the range {lower}-{upper}"
    return True


def input_number(
    message: str,
    default: Optional[int] = None,
    default_format: Optional[Callable[[int], str]] = None,
    default_pad: Optional[int] = None,
    lower: Optional[int] = 0,
    upper: Optional[int] = None,
    unknown: bool = False,
) -> Optional[int]:
    if default is None:
        default_string = ""
    else:
        if default_format:
            default_string = default_format(default)
        else:
            default_string = str(default)
        if default_pad:
            default_string = str(default).rjust(default_pad, "0")
    validation_fn: Callable[[str], bool | str] = lambda x: number_in_range(
        x, lower, upper, unknown
    )
    result = text(
        f"{message}", default=default_string, validate=validation_fn
    ).ask()
    if result is None:
        return None
    if result == "":
        return None
    return int(result)


def input_year(
    message: str = "Year", default: Optional[int] = None, unknown: bool = False
) -> Optional[int]:
    now = datetime.now()
    if default is not None:
        default_year = default
    else:
        default_year = now.year
    return input_number(
        message,
        default=default_year,
        default_pad=4,
        lower=0,
        upper=now.year,
        unknown=unknown,
    )


def input_month(
    message: str = "Month", default: Optional[int] = None, unknown: bool = False
) -> Optional[int]:
    now = datetime.now()
    if default is not None:
        default_month = default
    else:
        default_month = now.month
    return input_number(
        message,
        default=default_month,
        default_pad=2,
        lower=1,
        upper=12,
        unknown=unknown,
    )


def get_month_length(month: int, year: int) -> int:
    """
    Get the length of a month in days, for a given year
    """
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    elif month in [4, 6, 9, 11]:
        return 30
    elif year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        return 29
    else:
        return 28


def input_day(
    month: int,
    year: int,
    message: str = "Date",
    default: Optional[int] = None,
    unknown: bool = False,
) -> Optional[int]:
    max_days = get_month_length(month, year)
    now = datetime.now()
    if default is not None:
        default_day = default
    else:
        default_day = now.day
    return input_number(
        message,
        default=default_day,
        default_pad=2,
        lower=1,
        upper=max_days,
        unknown=unknown,
    )


def string_is_time(x: str) -> bool:
    if not len(x) == 4:
        return False
    if not x.isnumeric():
        return False
    num = int(x)
    if num > 2359 or num < 0:
        return False
    if num % 100 > 59:
        return False
    return True


def input_time(
    message: str = "Time",
    default: Optional[datetime] = None,
    unknown: bool = False,
) -> Optional[datetime]:
    if default is None:
        default_time = ""
    else:
        default_time = str(int(default.strftime("%H%M"))).rjust(4, "0")
    result = text(message, default=default_time, validate=string_is_time).ask()
    if result is None:
        return None
    else:
        time_string = str(result).rjust(4, "0")
        time_candidate = datetime.strptime(time_string, "%H%M")
        return time_candidate


def input_confirm(message: str, default: bool = True) -> bool:
    return ask_bool_question(message, default)


@dataclass
class PickSingle[T]:
    choice: T


@dataclass
class PickMultiple[T]:
    choices: list[T]


@dataclass
class PickUnknown:
    pass


@dataclass
class PickCancel:
    pass


type PickChoice[T] = PickSingle[T] | PickMultiple[T] | PickUnknown | PickCancel


def choice_from_object[T](
    object: T, display: Optional[Callable[[T], str]]
) -> Choice:
    if display is None:
        title = str(object)
    else:
        title = display(object)
    return Choice(title=title, value=PickSingle(object))


def input_select[T](
    message: str,
    choices: list[T],
    display: Optional[Callable[[T], str]] = None,
    cancel: bool = False,
    unknown: bool = False,
) -> Optional[PickChoice[T]]:
    choice_objects = [choice_from_object(choice, display) for choice in choices]
    if cancel:
        choice_objects.append(Choice(title="Cancel", value=PickCancel()))
    if unknown:
        choice_objects.append(Choice(title="Unknown", value=PickUnknown()))
    return ask_select_question(
        message, choice_objects, use_shortcuts=True, instruction=""
    )


def input_select_paginate[T](
    message: str, choices: list[T], display: Optional[Callable[[T], str]] = None
) -> Optional[PickChoice[T]]:
    partitions: list[list[T]] = []
    size_of_partition = 34
    number_of_partitions = ceil(len(choices) / size_of_partition)
    for i in range(0, number_of_partitions):
        current_partition: list[T] = []
        for j in range(0, size_of_partition):
            choice_index = i * size_of_partition + j
            if choice_index >= len(choices):
                break
            current_partition.append(choices[i * size_of_partition + j])
        partitions.append(current_partition)
    for i, partition in enumerate(partitions):
        choice_objects = [
            choice_from_object(choice, display) for choice in partition
        ]
        if i != len(partitions) - 1:
            choice_objects.append(Choice(title="Next", value=PickUnknown()))
        choice_objects.append(Choice(title="Cancel", value=PickCancel()))
        page_choice: PickChoice[T] = ask_select_question(
            message, choice_objects, use_shortcuts=True, instruction=""
        )
        match (page_choice):
            case PickUnknown():
                continue
            case _:
                return page_choice
    return None


def input_checkbox[T](
    message: str,
    choices: list[T],
    display: Optional[Callable[[T], str]] = None,
    allow_none: bool = False,
) -> Optional[PickMultiple[T]]:
    choice_objects = [choice_from_object(choice, display) for choice in choices]
    result: Optional[list[PickChoice[T]]] = checkbox(
        message, choice_objects
    ).ask()
    if result is None:
        return None
    answers: list[T] = []
    if not allow_none and len(result) == 0:
        return None
    for res in result:
        match res:
            case PickSingle(choice):
                answers.append(choice)
            case _:
                pass
    return PickMultiple(answers)


def input_datetime(start: Optional[datetime] = None) -> datetime:
    if start is not None:
        default_year = start.year
        default_month = start.month
        default_day = start.day
        default_time = start
    else:
        default_year = None
        default_month = None
        default_day = None
        default_time = None
    year = input_year(default=default_year)
    if year is None:
        raise RuntimeError()
    month = input_month(default=default_month)
    if month is None:
        raise RuntimeError()
    date = input_day(month, year, default=default_day)
    if date is None:
        raise RuntimeError()
    time = input_time(default=default_time)
    if time is None:
        raise RuntimeError()
    input_datetime = datetime(year, month, date, time.hour, time.minute)
    return make_timezone_aware(input_datetime)

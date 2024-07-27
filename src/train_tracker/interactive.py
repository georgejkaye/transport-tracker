from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional
from questionary import Choice, confirm, select, text
from termcolor import colored


def thick_line(length: int = 80):
    print("=" * length)


def thin_line(length: int = 80):
    print("-" * length)


def space():
    print()


def message(msg: str):
    print(msg)


def option(number: int, choice: str):
    print(f"{number}: {choice}")


def header(msg: str, length: int = 80):
    thick_line(length)
    message(msg)
    thick_line(length)
    space()


def subheader(msg: str, length: int = 80):
    thin_line(length)
    message(msg)
    thin_line(length)
    space()


def information(msg: str, end: str | None = None):
    exclamation = colored("!", "dark_grey")
    message = colored(msg, attrs=["bold"])
    print(f"{exclamation} {message}", end=end)


def input_text(message: str, default: str = "") -> Optional[str]:
    return text(message=message, default=default).ask()


def number_in_range(
    input: str, lower: Optional[int], upper: Optional[int], unknown: bool = False
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
    result = text(
        f"{message}",
        default=default_string,
        validate=lambda x: number_in_range(x, lower, upper, unknown),
    ).ask()
    if result == "":
        return None
    else:
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


def get_month_length(month, year):
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


def input_time(
    message: str = "Time",
    default: Optional[datetime] = None,
    unknown: bool = False,
) -> Optional[datetime]:
    now = datetime.now()
    if default is None:
        default_time = None
    else:
        default_time = int(default.strftime("%H%M"))
    result = input_number(
        message,
        default=default_time,
        lower=0,
        upper=2359,
        default_pad=4,
        unknown=unknown,
    )
    if result is None:
        return None
    else:
        time_string = str(result).rjust(4, "0")
        time_candidate = datetime.strptime(time_string, "%H%M")
        return time_candidate


def input_confirm(message: str, default: bool = True) -> bool:
    return confirm(message, default=default).ask()


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


def choice_from_object[T](object: T, display: Optional[Callable[[T], str]]) -> Choice:
    if display is None:
        title = str(object)
    else:
        title = display(object)
    return Choice(title=title, value=PickSingle(object))


def input_select[
    T
](
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
    return select(message, choice_objects, use_shortcuts=True, instruction="").ask()

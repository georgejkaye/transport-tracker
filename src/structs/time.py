from enum import Enum
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Optional

# How many minutes late/early is 'very' late/early
very: int = 5


class OnTimeStatus(Enum):
    VERY_EARLY = "very-early"
    EARLY = "early"
    ON_TIME = "on-time"
    LATE = "late"
    VERY_LATE = "very-late"
    UNKNOWN = "unknown"


@dataclass
class PlanActTime:
    plan: datetime
    act: Optional[datetime]
    diff: int
    status: OnTimeStatus


def get_diff(a: datetime, b: datetime) -> int:
    c = a - b
    return int(c.total_seconds() / 60.0)


def get_status(diff: int) -> OnTimeStatus:
    if diff <= -very:
        return OnTimeStatus.VERY_EARLY
    if diff < 0:
        return OnTimeStatus.EARLY
    if diff == 0:
        return OnTimeStatus.ON_TIME
    if diff < very:
        return OnTimeStatus.LATE
    return OnTimeStatus.VERY_LATE


def make_planact(date: date, plan: str, act: Optional[str]):
    plan_time = datetime.strptime(plan, "%H%M")
    plan_datetime = datetime.combine(date, plan_time.time())

    if act is not None:
        act_time = datetime.strptime(act, "%H%M")
        act_datetime = datetime.combine(date, act_time.time())
        diff = get_diff(act_datetime, plan_datetime)
        status = get_status(diff)
    else:
        diff = 0
        status = OnTimeStatus.UNKNOWN
        act_datetime = None
    return PlanActTime(
        plan_datetime,
        act_datetime,
        diff,
        status
    )


def add(dt: datetime, delta: int):
    return dt + timedelta(minutes=delta)


def pad_front(string, length):
    """
    Add zeroes to the front of a number string until it is the desired length
    """
    string = str(string)
    return "0" * (length - len(string)) + string


def get_hourmin_string(datetime: datetime | time, colon: bool = False):
    string = pad_front(datetime.hour, 2)
    if colon:
        string = string + " : "
    string = string + pad_front(datetime.minute, 2)
    return string


def get_duration_string(td: timedelta):
    return f"{pad_front(str(td.seconds // 3600), 2)}:{pad_front(str((td.seconds//60) % 60), 2)}"


def get_hour(datetime: datetime):
    return pad_front(datetime.hour, 2)


def get_mins(datetime: datetime):
    return pad_front(datetime.minute, 2)


def get_year(datetime: datetime | date):
    return str(datetime.year)


def get_month(datetime: datetime | date):
    return pad_front(datetime.month, 2)


def get_day(datetime: datetime | date):
    return pad_front(datetime.day, 2)


def get_url(datetime: datetime, long: bool = True):
    string = get_year(datetime) + "/" + \
        get_month(datetime) + "/" + get_day(datetime)
    if long:
        string = string + "/" + get_hourmin_string(datetime)
    return string


def get_diff_string(diff: int):
    if diff > 0:
        return f"+{diff}"
    if diff < 0:
        return f"{diff}"
    return "0"


def get_diff_struct(diff: int):
    string = get_diff_string(diff)
    status = get_status(diff)
    return {
        "diff": string,
        "status": status
    }


def get_duration(start: time, end: time) -> timedelta:
    start_datetime = datetime.combine(date.today(), start)
    end_datetime = datetime.combine(date.today(), end)

    if end_datetime <= start_datetime:
        start_datetime = start_datetime + timedelta(1)

    return end_datetime - start_datetime


def to_time(str: str):
    return time(int(str[0:2]), int(str[2:4]))


def timedelta_from_string(str):
    parts = str.split(":")
    hour = int(parts[0])
    minutes = int(parts[1])
    return timedelta(hours=hour, minutes=minutes)


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

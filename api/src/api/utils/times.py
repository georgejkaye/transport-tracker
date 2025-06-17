import zoneinfo
from datetime import date, datetime, time, timedelta
from typing import Any, Optional

import pytz

from api.utils.environment import get_env_variable

timezone_variable = get_env_variable("TIMEZONE")
if timezone_variable is None or timezone_variable not in pytz.all_timezones_set:
    timezone_variable = "Europe/London"

utc = zoneinfo.ZoneInfo("UTC")
local_timezone = zoneinfo.ZoneInfo(timezone_variable)


def get_local_timezone() -> zoneinfo.ZoneInfo:
    return local_timezone


very = 5


def get_status(diff: int) -> str:
    if diff <= -very:
        return "very-early"
    if diff < 0:
        return "early"
    if diff == 0:
        return "on-time"
    if diff < very:
        return "late"
    return "very-late"


def add(dt: datetime, delta: int) -> datetime:
    return dt + timedelta(minutes=delta)


def pad_front(value: Any, length: int) -> str:
    """
    Add zeroes to the front of a number string until it is the desired length
    """
    string = str(value)
    return "0" * (length - len(string)) + string


def get_hourmin_string(
    datetime: datetime | time | None, colon: bool = False
) -> str:
    if datetime is None:
        return "-"
    string = pad_front(datetime.hour, 2)
    if colon:
        string = string + " : "
    string = string + pad_front(datetime.minute, 2)
    return string


def get_duration_string(td: timedelta) -> str:
    return f"{pad_front(str(td.seconds // 3600), 2)}:{pad_front(str((td.seconds//60) % 60), 2)}"


def get_hour(datetime: datetime) -> str:
    return pad_front(datetime.hour, 2)


def get_mins(datetime: datetime) -> str:
    return pad_front(datetime.minute, 2)


def get_year(datetime: datetime | date) -> str:
    return str(datetime.year)


def get_month(datetime: datetime | date) -> str:
    return pad_front(datetime.month, 2)


def get_day(datetime: datetime | date) -> str:
    return pad_front(datetime.day, 2)


def get_url(datetime: datetime, long: bool = True) -> str:
    string = (
        get_year(datetime) + "/" + get_month(datetime) + "/" + get_day(datetime)
    )
    if long:
        string = string + "/" + get_hourmin_string(datetime)
    return string


def get_datetime_route(dt: datetime, include_time: bool) -> str:
    string = get_year(dt) + "/" + get_month(dt) + "/" + get_day(dt)
    if include_time:
        string = string + "/" + get_hourmin_string(dt)
    return string


def get_diff_string(diff: int) -> str:
    if diff > 0:
        return f"+{diff}"
    if diff < 0:
        return f"{diff}"
    return "0"


def get_duration(start: time, end: time) -> timedelta:
    start_datetime = datetime.combine(date.today(), start)
    end_datetime = datetime.combine(date.today(), end)

    if end_datetime <= start_datetime:
        start_datetime = start_datetime + timedelta(1)

    return end_datetime - start_datetime


def to_time(str: str) -> time:
    return time(int(str[0:2]), int(str[2:4]))


def make_timezone_aware(
    datetime: datetime, tz: zoneinfo.ZoneInfo = local_timezone
) -> datetime:
    return datetime.replace(tzinfo=tz)


def change_timezone(
    datetime: Optional[datetime],
    source_tz: zoneinfo.ZoneInfo = utc,
    target_tz: zoneinfo.ZoneInfo = local_timezone,
) -> Optional[datetime]:
    if datetime is None:
        return None
    source_time = make_timezone_aware(datetime, source_tz)
    target_time = source_time.astimezone(target_tz)
    return target_time

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta


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


def get_year(datetime: datetime):
    return str(datetime.year)


def get_month(datetime: datetime):
    return pad_front(datetime.month, 2)


def get_day(datetime: datetime):
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


def get_duration(start: time, end: time) -> datetime:
    start = datetime.combine(date.today(), start)
    end = datetime.combine(date.today(), end)

    if end <= start:
        end = end + timedelta(1)

    return end - start


def to_time(str: str):
    return time(int(str[0:2]), int(str[2:4]))

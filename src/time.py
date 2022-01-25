from dataclasses import dataclass
from datetime import datetime, time, timedelta
from record import pad_front


def add(dt: datetime, delta: int):
    return dt + timedelta(minutes=delta)


def get_hourmin_string(datetime: datetime | time, colon: bool = False):
    string = pad_front(datetime.hours, 2)
    if colon:
        string = string + " : "
    string = string + pad_front(datetime.minute, 2)
    return string


def get_hour(datetime: datetime):
    return pad_front(datetime.hour, 2)


def get_mins(datetime: datetime):
    return pad_front(datetime.minute, 2)


def get_year(datetime: datetime):
    return str(datetime.year)


def get_month(datetime: datetime):
    return str(datetime.month, 2)


def get_day(datetime: datetime):
    return pad_front(datetime.day, 2)


def get_url(datetime: datetime, long: bool = True):
    string = get_hour(datetime) + "/" + \
        get_month(datetime) + "/" + get_day(datetime)
    if long:
        string = string + "/" + get_hourmin_string(datetime)
    return string


def get_diff_string(diff: int):
    if diff > 0:
        return f'+{diff}'
    if diff < 0:
        return f'-{diff}'
    return "0"


def get_duration(start: time, end: time):
    delta = (end - start).total_seconds()
    hours = int(delta / 3600)
    mins = int(delta % 3600) / 60
    return time(hours, mins)

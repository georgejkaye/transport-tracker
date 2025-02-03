from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from api.utils.database import register_type
from psycopg import Connection


@dataclass
class LegStat:
    leg_id: int
    board_time: datetime
    board_crs: str
    board_name: str
    alight_time: datetime
    alight_crs: str
    alight_name: str
    distance: Decimal
    duration: timedelta
    delay: int
    operator_id: int
    operator_name: str
    is_brand: bool


@dataclass
class StationStat:
    station_crs: str
    station_name: str
    boards: int
    alights: int
    intermediates: int


@dataclass
class OperatorStat:
    operator_id: int
    operator_name: str
    is_brand: bool
    count: int
    distance: Decimal
    duration: timedelta
    delay: int


@dataclass
class UnitStat:
    stock_number: int
    count: int
    distance: Decimal
    duration: timedelta


@dataclass
class ClassStat:
    stock_class: int
    count: int
    distance: Decimal
    duration: timedelta


@dataclass
class Stats:
    journeys: int
    distance: Decimal
    duration: timedelta
    delay: int
    leg_stats: list[LegStat]
    station_stats: list[StationStat]
    operator_stats: list[OperatorStat]
    class_stats: list[ClassStat]
    unit_stats: list[UnitStat]


def register_leg_stat(
    leg_id: int,
    board_time: datetime,
    board_crs: str,
    board_name: str,
    alight_time: datetime,
    alight_crs: str,
    alight_name: str,
    distance: Decimal,
    duration: timedelta,
    delay: int,
    operator_id: int,
    operator_name: str,
    is_brand: bool,
):
    return LegStat(
        leg_id,
        board_time,
        board_crs,
        board_name,
        alight_time,
        alight_crs,
        alight_name,
        distance,
        duration,
        delay,
        operator_id,
        operator_name,
        is_brand,
    )


def register_station_stat(
    station_crs: str,
    station_name: str,
    boards: int,
    alights: int,
    intermediates: int,
):
    return StationStat(
        station_crs, station_name, boards, alights, intermediates
    )


def register_operator_stat(
    operator_id: int,
    operator_name: str,
    is_brand: bool,
    count: int,
    distance: Decimal,
    duration: timedelta,
    delay: int,
):
    return OperatorStat(
        operator_id, operator_name, is_brand, count, distance, duration, delay
    )


def register_class_stat(
    stock_class: int, count: int, distance: Decimal, duration: timedelta
):
    return ClassStat(stock_class, count, distance, duration)


def register_unit_stat(
    stock_unit: int, count: int, distance: Decimal, duration: timedelta
):
    return UnitStat(stock_unit, count, distance, duration)


def register_stats(
    journeys: int,
    distance: Decimal,
    duration: timedelta,
    delay: int,
    leg_stats: list[LegStat],
    station_stats: list[StationStat],
    operator_stats: list[OperatorStat],
    class_stats: list[ClassStat],
    unit_stats: list[UnitStat],
):
    return Stats(
        journeys,
        distance,
        duration,
        delay,
        leg_stats,
        station_stats,
        operator_stats,
        class_stats,
        unit_stats,
    )


def get_train_stats(
    conn: Connection,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
) -> Stats:
    register_type(conn, "OutLegStat", register_leg_stat)
    register_type(conn, "OutStationStat", register_station_stat)
    register_type(conn, "OutOperatorStat", register_operator_stat)
    register_type(conn, "OutClassStat", register_class_stat)
    register_type(conn, "OutUnitStat", register_unit_stat)
    register_type(conn, "OutStats", register_stats)

    row = conn.execute(
        "SELECT GetStats(%s, %s)", [search_start, search_end]
    ).fetchone()
    if row is None:
        raise RuntimeError("Could not get stats")
    return row[0]

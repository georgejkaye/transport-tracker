from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from psycopg import Connection
from psycopg.rows import class_row

from api.utils.database import register_type


@dataclass
class LegStat:
    leg_id: int
    user_id: int
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
    operator_code: str
    operator_name: str
    is_brand: bool


def register_leg_stat(
    leg_id: int,
    user_id: int,
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
    operator_code: str,
    operator_name: str,
    is_brand: bool,
) -> LegStat:
    return LegStat(
        leg_id,
        user_id,
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
        operator_code,
        operator_name,
        is_brand,
    )


@dataclass
class StationStat:
    station_crs: str
    station_name: str
    operator_id: int
    operator_name: str
    is_brand: bool
    boards: int
    alights: int
    intermediates: int


def register_station_stat(
    station_crs: str,
    station_name: str,
    operator_name: str,
    operator_id: int,
    is_brand: bool,
    boards: int,
    alights: int,
    intermediates: int,
) -> StationStat:
    return StationStat(
        station_crs,
        station_name,
        operator_id,
        operator_name,
        is_brand,
        boards,
        alights,
        intermediates,
    )


@dataclass
class OperatorStat:
    operator_id: int
    operator_name: str
    is_brand: bool
    count: int
    distance: Decimal
    duration: timedelta
    delay: int


def register_operator_stat(
    operator_id: int,
    operator_name: str,
    is_brand: bool,
    count: int,
    distance: Decimal,
    duration: timedelta,
    delay: int,
) -> OperatorStat:
    return OperatorStat(
        operator_id, operator_name, is_brand, count, distance, duration, delay
    )


@dataclass
class UnitStat:
    stock_number: int
    count: int
    distance: Decimal
    duration: timedelta


def register_unit_stat(
    stock_unit: int, count: int, distance: Decimal, duration: timedelta
) -> UnitStat:
    return UnitStat(stock_unit, count, distance, duration)


@dataclass
class ClassStat:
    stock_class: int
    count: int
    distance: Decimal
    duration: timedelta


def register_class_stat(
    stock_class: int, count: int, distance: Decimal, duration: timedelta
) -> ClassStat:
    return ClassStat(stock_class, count, distance, duration)


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
) -> Stats:
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


def register_stats_types(conn: Connection) -> None:
    register_type(conn, "OutLegStat", register_leg_stat)
    register_type(conn, "OutStationStat", register_station_stat)
    register_type(conn, "OutOperatorStat", register_operator_stat)
    register_type(conn, "OutClassStat", register_class_stat)
    register_type(conn, "OutUnitStat", register_unit_stat)
    register_type(conn, "OutStats", register_stats)


def get_train_stats(
    conn: Connection,
    user_id: int,
    search_start: Optional[datetime] = None,
    search_end: Optional[datetime] = None,
) -> Stats:
    register_stats_types(conn)
    with conn.cursor(row_factory=class_row(Stats)) as cur:
        row = cur.execute(
            "SELECT GetStats(%s, %s, %s)", [user_id, search_start, search_end]
        ).fetchone()
        if row is None:
            raise RuntimeError("Could not get stats")
        return row

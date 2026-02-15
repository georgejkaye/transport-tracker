from datetime import datetime
from typing import Optional

from psycopg import Connection

from api.classes.train.stats import TrainStats
from api.db.functions.select.train.user.leg import (
    select_longest_delay_transport_user_train_legs_by_user_id_fetchall,
    select_longest_distance_transport_user_train_legs_by_user_id_fetchall,
    select_longest_duration_transport_user_train_legs_by_user_id_fetchall,
    select_shortest_delay_transport_user_train_legs_by_user_id_fetchall,
    select_shortest_distance_transport_user_train_legs_by_user_id_fetchall,
    select_shortest_duration_transport_user_train_legs_by_user_id_fetchall,
)
from api.db.functions.select.train.user.operator import (
    select_top_transport_user_train_operators_by_user_id_fetchall,
)
from api.db.functions.select.train.user.vehicle import (
    select_top_transport_user_train_classes_by_user_id_fetchall,
    select_top_transport_user_train_units_by_user_id_fetchall,
    select_transport_user_train_class_stats_by_user_id_fetchone,
    select_transport_user_train_unit_stats_by_user_id_fetchone,
)
from api.db.functions.select.user.stats import (
    select_transport_user_details_fetchone,
)
from api.db.types.user.user import (
    TransportUserDetailsTrainLegOutData,
    TransportUserDetailsTrainStationOutData,
    TransportUserDetailsTrainYearOutData,
    TransportUserTrainOperatorStats,
)
from api.stats.classes.train import (
    UserTrainAllStats,
    UserTrainStats,
    UserTrainYearStats,
)
from api.stats.classes.user import UserDetails


def transform_train_stats(
    train_stats: TransportUserDetailsTrainYearOutData,
) -> UserTrainAllStats:
    years = [yearly_stat.year for yearly_stat in train_stats.leg_stats_yearly]
    year_stats = [
        UserTrainYearStats(
            year,
            TransportUserDetailsTrainLegOutData(
                train_stats.leg_stats_yearly[i].count,
                train_stats.leg_stats_yearly[i].total_distance,
                train_stats.leg_stats_yearly[i].longest_distance,
                train_stats.leg_stats_yearly[i].shortest_distance,
                train_stats.leg_stats_yearly[i].total_duration,
                train_stats.leg_stats_yearly[i].longest_duration,
                train_stats.leg_stats_yearly[i].shortest_duration,
                train_stats.leg_stats_yearly[i].total_delay,
                train_stats.leg_stats_yearly[i].longest_delay,
                train_stats.leg_stats_yearly[i].shortest_delay,
            ),
            TransportUserDetailsTrainStationOutData(
                train_stats.station_stats_yearly[i].station_count,
                train_stats.station_stats_yearly[i].new_station_count,
                train_stats.station_stats_yearly[
                    i
                ].most_boards_and_alights_station,
                train_stats.station_stats_yearly[i].most_boards_station,
                train_stats.station_stats_yearly[i].most_alights_station,
                train_stats.station_stats_yearly[i].most_calls_station,
            ),
            TransportUserTrainOperatorStats(
                train_stats.operator_stats_yearly[i].operator_count,
                train_stats.operator_stats_yearly[i].greatest_count,
                train_stats.operator_stats_yearly[i].least_count,
                train_stats.operator_stats_yearly[i].longest_distance,
                train_stats.operator_stats_yearly[i].shortest_distance,
                train_stats.operator_stats_yearly[i].longest_duration,
                train_stats.operator_stats_yearly[i].shortest_duration,
                train_stats.operator_stats_yearly[i].longest_delay,
                train_stats.operator_stats_yearly[i].shortest_delay,
            ),
        )
        for (i, year) in enumerate(years)
    ]

    return UserTrainAllStats(
        UserTrainStats(
            train_stats.leg_stats_overall,
            train_stats.station_stats_overall,
            train_stats.operator_stats_overall,
        ),
        year_stats,
    )


def get_user_details(conn: Connection, user_id: int) -> Optional[UserDetails]:
    raw_user_details = select_transport_user_details_fetchone(conn, user_id)
    if raw_user_details is None:
        return None
    train_stats = transform_train_stats(raw_user_details.train_stats)
    return UserDetails(
        raw_user_details.user_id,
        raw_user_details.user_name,
        raw_user_details.display_name,
        train_stats,
    )


def get_train_stats(
    conn: Connection,
    user_id: int,
    search_start: datetime,
    search_end: datetime,
    rows_to_return: int = 4,
    operators_by_brands: bool = True,
) -> Optional[TrainStats]:
    longest_distance_legs = (
        select_longest_distance_transport_user_train_legs_by_user_id_fetchall(
            conn, user_id, search_start, search_end, rows_to_return
        )
    )
    shortest_distance_legs = (
        select_shortest_distance_transport_user_train_legs_by_user_id_fetchall(
            conn, user_id, search_start, search_end, rows_to_return
        )
    )
    longest_duration_legs = (
        select_longest_duration_transport_user_train_legs_by_user_id_fetchall(
            conn, user_id, search_start, search_end, rows_to_return
        )
    )
    shortest_duration_legs = (
        select_shortest_duration_transport_user_train_legs_by_user_id_fetchall(
            conn, user_id, search_start, search_end, rows_to_return
        )
    )
    longest_delay_legs = (
        select_longest_delay_transport_user_train_legs_by_user_id_fetchall(
            conn, user_id, search_start, search_end, rows_to_return
        )
    )
    shortest_delay_legs = (
        select_shortest_delay_transport_user_train_legs_by_user_id_fetchall(
            conn, user_id, search_start, search_end, rows_to_return
        )
    )
    leg_stats = (
        select_transport_user_train_leg_stats_numbers_by_user_id_fetchone(
            conn, user_id, search_start, search_end
        )
    )
    if leg_stats is None:
        return None
    operator_stats = (
        select_transport_user_train_operator_stats_by_user_id_fetchone(
            conn, user_id, operators_by_brands, search_start, search_end
        )
    )
    if operator_stats is None:
        return None
    top_operators = (
        select_top_transport_user_train_operators_by_user_id_fetchall(
            conn,
            user_id,
            operators_by_brands,
            search_start,
            search_end,
            rows_to_return,
        )
    )
    class_stats = select_transport_user_train_class_stats_by_user_id_fetchone(
        conn, user_id, search_start, search_end
    )
    if class_stats is None:
        return None
    top_classes = select_top_transport_user_train_classes_by_user_id_fetchall(
        conn, user_id, search_start, search_end, rows_to_return
    )
    unit_stats = select_transport_user_train_unit_stats_by_user_id_fetchone(
        conn, user_id, search_start, search_end
    )
    if unit_stats is None:
        return None
    top_units = select_top_transport_user_train_units_by_user_id_fetchall(
        conn, user_id, search_start, search_end, rows_to_return
    )
    return TrainStats(
        leg_stats.count,
        leg_stats.total_distance,
        leg_stats.longest_distance,
        longest_distance_legs,
        leg_stats.shortest_distance,
        shortest_distance_legs,
        leg_stats.total_duration,
        leg_stats.longest_duration,
        longest_duration_legs,
        leg_stats.shortest_duration,
        shortest_duration_legs,
        leg_stats.total_delay,
        leg_stats.longest_delay,
        longest_delay_legs,
        leg_stats.shortest_delay,
        shortest_delay_legs,
        operator_stats.count,
        top_operators,
        class_stats.count,
        top_classes,
        unit_stats.count,
        top_units,
    )

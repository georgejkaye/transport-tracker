from datetime import datetime
from typing import Optional

from psycopg import Connection

from api.classes.train.stats import TrainStats
from api.db.functions.select.train.user.leg import (
    select_transport_user_train_leg_stats_by_user_id_fetchone,
)
from api.db.functions.select.train.user.operator import (
    select_top_transport_user_train_operators_by_user_id_fetchall,
    select_transport_user_train_operator_stats_by_user_id_fetchone,
)
from api.db.functions.select.train.user.vehicle import (
    select_top_transport_user_train_classes_by_user_id_fetchall,
    select_top_transport_user_train_units_by_user_id_fetchall,
    select_transport_user_train_class_stats_by_user_id_fetchone,
    select_transport_user_train_unit_stats_by_user_id_fetchone,
)


def get_train_stats(
    conn: Connection,
    user_id: int,
    search_start: datetime,
    search_end: datetime,
    rows_to_return: int = 4,
    operators_by_brands: bool = True,
) -> Optional[TrainStats]:
    leg_stats = select_transport_user_train_leg_stats_by_user_id_fetchone(
        conn, user_id, search_start, search_end, rows_to_return
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
        leg_stats.longest_distance_legs,
        leg_stats.shortest_distance,
        leg_stats.shortest_distance_legs,
        leg_stats.total_duration,
        leg_stats.longest_duration,
        leg_stats.longest_duration_legs,
        leg_stats.shortest_duration,
        leg_stats.shortest_duration_legs,
        leg_stats.total_delay,
        leg_stats.longest_delay,
        leg_stats.longest_delay_legs,
        leg_stats.shortest_delay,
        leg_stats.shortest_delay_legs,
        operator_stats.count,
        top_operators,
        class_stats.count,
        top_classes,
        unit_stats.count,
        top_units,
    )

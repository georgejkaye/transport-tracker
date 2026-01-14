DROP FUNCTION IF EXISTS select_transport_user_train_leg_stats_numbers_by_user_id CASCADE;
DROP FUNCTION IF EXISTS select_transport_user_train_stats_numbers_by_user_id CASCADE;

CREATE FUNCTION select_transport_user_train_leg_stats_numbers_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_details_train_leg_out_data
LANGUAGE sql
AS
$$
WITH
transport_user_train_leg_stat AS (
    SELECT
        train_leg_id,
        (board_station).station_name
            || ' to '
            || (alight_station).station_name
            AS description,
        distance,
        duration,
        delay,
        start_datetime
    FROM transport_user_train_leg_view
    WHERE user_id = p_user_id
    AND (p_search_start IS NULL OR start_datetime >= p_search_start)
    AND (p_search_end IS NULL OR start_datetime < p_search_end)
),
transport_user_train_leg_distance_stat AS (
    SELECT
        distance,
        train_leg_id,
        description,
        start_datetime
    FROM (
        SELECT
            distance,
            train_leg_id,
            description,
            start_datetime,
            ROW_NUMBER() OVER (
                PARTITION BY distance
                ORDER BY start_datetime
            ) AS rownum
        FROM transport_user_train_leg_stat
    ) WHERE rownum = 1
),
transport_user_train_leg_duration_stat AS (
    SELECT
        duration,
        train_leg_id,
        description,
        start_datetime
    FROM (
        SELECT
            duration,
            train_leg_id,
            description,
            start_datetime,
            ROW_NUMBER() OVER (
                PARTITION BY distance
                ORDER BY start_datetime
            ) AS rownum
        FROM transport_user_train_leg_stat
    ) WHERE rownum = 1
),
transport_user_train_leg_delay_stat AS (
    SELECT
        delay,
        train_leg_id,
        description,
        start_datetime
    FROM (
        SELECT
            delay,
            train_leg_id,
            description,
            start_datetime,
            ROW_NUMBER() OVER (
                PARTITION BY delay
                ORDER BY start_datetime
            ) AS rownum
        FROM transport_user_train_leg_stat
    ) WHERE rownum = 1
)
SELECT
    transport_user_train_leg_stats_view.count,
    transport_user_train_leg_stats_view.total_distance,
    (
        transport_user_train_leg_distance_stat_longest.distance,
        transport_user_train_leg_distance_stat_longest.train_leg_id,
        transport_user_train_leg_distance_stat_longest.description,
        transport_user_train_leg_distance_stat_longest.start_datetime
    )::transport_user_details_decimal_timestamp_stat,
    (
        transport_user_train_leg_distance_stat_shortest.distance,
        transport_user_train_leg_distance_stat_shortest.train_leg_id,
        transport_user_train_leg_distance_stat_shortest.description,
        transport_user_train_leg_distance_stat_shortest.start_datetime
    )::transport_user_details_decimal_timestamp_stat,
    transport_user_train_leg_stats_view.total_duration,
    (
        transport_user_train_leg_duration_stat_longest.duration,
        transport_user_train_leg_duration_stat_longest.train_leg_id,
        transport_user_train_leg_duration_stat_longest.description,
        transport_user_train_leg_duration_stat_longest.start_datetime
    )::transport_user_details_interval_timestamp_stat,
    (
        transport_user_train_leg_duration_stat_shortest.duration,
        transport_user_train_leg_duration_stat_shortest.train_leg_id,
        transport_user_train_leg_duration_stat_shortest.description,
        transport_user_train_leg_duration_stat_shortest.start_datetime
    )::transport_user_details_interval_timestamp_stat,
    transport_user_train_leg_stats_view.total_delay,
    (
        transport_user_train_leg_delay_stat_longest.delay,
        transport_user_train_leg_delay_stat_longest.train_leg_id,
        transport_user_train_leg_delay_stat_longest.description,
        transport_user_train_leg_delay_stat_longest.start_datetime
    )::transport_user_details_integer_timestamp_stat,
    (
        transport_user_train_leg_delay_stat_shortest.delay,
        transport_user_train_leg_delay_stat_shortest.train_leg_id,
        transport_user_train_leg_delay_stat_shortest.description,
        transport_user_train_leg_delay_stat_shortest.start_datetime
    )::transport_user_details_integer_timestamp_stat
FROM (
    SELECT
        COUNT(*) AS count,
        SUM(distance) AS total_distance,
        MAX(distance) AS longest_distance,
        MIN(distance) AS shortest_distance,
        SUM(duration) AS total_duration,
        MAX(duration) AS longest_duration,
        MIN(duration) AS shortest_duration,
        SUM(delay) AS total_delay,
        MAX(delay) AS longest_delay,
        MIN(delay) AS shortest_delay
    FROM transport_user_train_leg_stat
) transport_user_train_leg_stats_view
INNER JOIN transport_user_train_leg_distance_stat
    transport_user_train_leg_distance_stat_longest
ON transport_user_train_leg_stats_view.longest_distance
    = transport_user_train_leg_distance_stat_longest.distance
INNER JOIN transport_user_train_leg_distance_stat
    transport_user_train_leg_distance_stat_shortest
ON transport_user_train_leg_stats_view.shortest_distance
    = transport_user_train_leg_distance_stat_shortest.distance
INNER JOIN transport_user_train_leg_duration_stat
    transport_user_train_leg_duration_stat_longest
ON transport_user_train_leg_stats_view.longest_duration
    = transport_user_train_leg_duration_stat_longest.duration
INNER JOIN transport_user_train_leg_duration_stat
    transport_user_train_leg_duration_stat_shortest
ON transport_user_train_leg_stats_view.longest_duration
    = transport_user_train_leg_duration_stat_shortest.duration
INNER JOIN transport_user_train_leg_delay_stat
    transport_user_train_leg_delay_stat_longest
ON transport_user_train_leg_stats_view.longest_delay
    = transport_user_train_leg_delay_stat_longest.delay
INNER JOIN transport_user_train_leg_delay_stat
    transport_user_train_leg_delay_stat_shortest
ON transport_user_train_leg_stats_view.shortest_delay
    = transport_user_train_leg_delay_stat_shortest.delay;
$$;

CREATE FUNCTION select_transport_user_train_stats_numbers_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS transport_user_details_train_out_data
LANGUAGE plpgsql
AS
$$
DECLARE
    v_train_leg_stats transport_user_details_train_leg_out_data;
    v_train_station_stats transport_user_details_train_station_out_data;
    v_train_operator_stats transport_user_details_train_operator_out_data;
    v_train_class_stats transport_user_details_train_class_out_data;
    v_train_unit_stats transport_user_details_train_unit_out_data;
BEGIN
    v_train_leg_stats :=
        select_transport_user_train_leg_stats_numbers_by_user_id(
            p_user_id,
            p_search_start,
            p_search_end
        );

    RETURN (
        1,
        v_train_leg_stats
    )::transport_user_details_train_out_data;
END;
$$;
DROP FUNCTION IF EXISTS select_transport_user_train_leg_stats_numbers_by_user_id CASCADE;
DROP FUNCTION IF EXISTS select_transport_user_train_stats_numbers_by_user_id CASCADE;
DROP FUNCTION IF EXISTS select_transport_user_train_leg_year_stats_by_user_id CASCADE;

CREATE FUNCTION select_transport_user_train_leg_stats_numbers_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_details_train_leg_period_out_data
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
RETURNS transport_user_details_out_data
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
    )::transport_user_details_out_data;
END;
$$;

CREATE FUNCTION select_transport_user_train_leg_year_stats_by_user_id (
    p_user_id INTEGER_NOTNULL
)
RETURNS SETOF transport_user_details_train_leg_year_out_data
LANGUAGE sql
AS
$$
WITH
transport_user_train_leg_stat AS (
    SELECT
        DATE_PART('year', start_datetime) AS year,
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
),
transport_user_train_leg_distance_stat AS (
    SELECT
        year,
        distance,
        train_leg_id,
        description,
        start_datetime
    FROM (
        SELECT
            year,
            distance,
            train_leg_id,
            description,
            start_datetime,
            ROW_NUMBER() OVER (
                PARTITION BY year, distance
                ORDER BY start_datetime
            ) AS rownum
        FROM transport_user_train_leg_stat
    ) WHERE rownum = 1
),
transport_user_train_leg_duration_stat AS (
    SELECT
        year,
        duration,
        train_leg_id,
        description,
        start_datetime
    FROM (
        SELECT
            year,
            duration,
            train_leg_id,
            description,
            start_datetime,
            ROW_NUMBER() OVER (
                PARTITION BY year, duration
                ORDER BY start_datetime
            ) AS rownum
        FROM transport_user_train_leg_stat
    ) WHERE rownum = 1
),
transport_user_train_leg_delay_stat AS (
    SELECT
        year,
        delay,
        train_leg_id,
        description,
        start_datetime
    FROM (
        SELECT
            year,
            delay,
            train_leg_id,
            description,
            start_datetime,
            ROW_NUMBER() OVER (
                PARTITION BY year, delay
                ORDER BY start_datetime
            ) AS rownum
        FROM transport_user_train_leg_stat
    ) WHERE rownum = 1
)
SELECT
    year,
    count,
    total_distance,
    longest_distance,
    shortest_distance,
    total_duration,
    longest_duration,
    shortest_duration,
    total_delay,
    longest_delay,
    shortest_delay
FROM (
    SELECT
        NULL AS year,
        transport_user_train_leg_stats_view.count,
        transport_user_train_leg_stats_view.total_distance,
        (
            transport_user_train_leg_distance_stat_longest.distance,
            transport_user_train_leg_distance_stat_longest.train_leg_id,
            transport_user_train_leg_distance_stat_longest.description,
            transport_user_train_leg_distance_stat_longest.start_datetime
        )::transport_user_details_decimal_timestamp_stat AS longest_distance,
        (
            transport_user_train_leg_distance_stat_shortest.distance,
            transport_user_train_leg_distance_stat_shortest.train_leg_id,
            transport_user_train_leg_distance_stat_shortest.description,
            transport_user_train_leg_distance_stat_shortest.start_datetime
        )::transport_user_details_decimal_timestamp_stat AS shortest_distance,
        transport_user_train_leg_stats_view.total_duration,
        (
            transport_user_train_leg_duration_stat_longest.duration,
            transport_user_train_leg_duration_stat_longest.train_leg_id,
            transport_user_train_leg_duration_stat_longest.description,
            transport_user_train_leg_duration_stat_longest.start_datetime
        )::transport_user_details_interval_timestamp_stat AS longest_duration,
        (
            transport_user_train_leg_duration_stat_shortest.duration,
            transport_user_train_leg_duration_stat_shortest.train_leg_id,
            transport_user_train_leg_duration_stat_shortest.description,
            transport_user_train_leg_duration_stat_shortest.start_datetime
        )::transport_user_details_interval_timestamp_stat AS shortest_duration,
        transport_user_train_leg_stats_view.total_delay,
        (
            transport_user_train_leg_delay_stat_longest.delay,
            transport_user_train_leg_delay_stat_longest.train_leg_id,
            transport_user_train_leg_delay_stat_longest.description,
            transport_user_train_leg_delay_stat_longest.start_datetime
        )::transport_user_details_integer_timestamp_stat AS longest_delay,
        (
            transport_user_train_leg_delay_stat_shortest.delay,
            transport_user_train_leg_delay_stat_shortest.train_leg_id,
            transport_user_train_leg_delay_stat_shortest.description,
            transport_user_train_leg_delay_stat_shortest.start_datetime
        )::transport_user_details_integer_timestamp_stat AS shortest_delay
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
    ON transport_user_train_leg_stats_view.shortest_duration
        = transport_user_train_leg_duration_stat_shortest.duration
    INNER JOIN transport_user_train_leg_delay_stat
        transport_user_train_leg_delay_stat_longest
    ON transport_user_train_leg_stats_view.longest_delay
        = transport_user_train_leg_delay_stat_longest.delay
    INNER JOIN transport_user_train_leg_delay_stat
        transport_user_train_leg_delay_stat_shortest
    ON transport_user_train_leg_stats_view.shortest_delay
        = transport_user_train_leg_delay_stat_shortest.delay
    UNION
    SELECT
        transport_user_train_leg_stats_view.year,
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
            year,
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
        GROUP BY year
    ) transport_user_train_leg_stats_view
    INNER JOIN transport_user_train_leg_distance_stat
        transport_user_train_leg_distance_stat_longest
    ON transport_user_train_leg_stats_view.longest_distance
        = transport_user_train_leg_distance_stat_longest.distance
    AND transport_user_train_leg_stats_view.year
        = transport_user_train_leg_distance_stat_longest.year
    INNER JOIN transport_user_train_leg_distance_stat
        transport_user_train_leg_distance_stat_shortest
    ON transport_user_train_leg_stats_view.shortest_distance
        = transport_user_train_leg_distance_stat_shortest.distance
    AND transport_user_train_leg_stats_view.year
        = transport_user_train_leg_distance_stat_shortest.year
    INNER JOIN transport_user_train_leg_duration_stat
        transport_user_train_leg_duration_stat_longest
    ON transport_user_train_leg_stats_view.longest_duration
        = transport_user_train_leg_duration_stat_longest.duration
    AND transport_user_train_leg_stats_view.year
        = transport_user_train_leg_duration_stat_longest.year
    INNER JOIN transport_user_train_leg_duration_stat
        transport_user_train_leg_duration_stat_shortest
    ON transport_user_train_leg_stats_view.shortest_duration
        = transport_user_train_leg_duration_stat_shortest.duration
    AND transport_user_train_leg_stats_view.year
        = transport_user_train_leg_duration_stat_shortest.year
    INNER JOIN transport_user_train_leg_delay_stat
        transport_user_train_leg_delay_stat_longest
    ON transport_user_train_leg_stats_view.longest_delay
        = transport_user_train_leg_delay_stat_longest.delay
    AND transport_user_train_leg_stats_view.year
        = transport_user_train_leg_delay_stat_longest.year
    INNER JOIN transport_user_train_leg_delay_stat
        transport_user_train_leg_delay_stat_shortest
    ON transport_user_train_leg_stats_view.shortest_delay
        = transport_user_train_leg_delay_stat_shortest.delay
    AND transport_user_train_leg_stats_view.year
        = transport_user_train_leg_delay_stat_shortest.year
)
ORDER BY year NULLS FIRST;
$$;

CREATE FUNCTION select_transport_user_train_operator_stats_years_by_user_id (
    p_user_id INTEGER_NOTNULL
)
RETURNS transport_user_details_train_operator_out_data
LANGUAGE sql
AS
$$
WITH
train_station_leg_view AS (
    SELECT
        year,
        train_station_id,
        COUNT(*) AS total,
        COUNT(
            CASE
            WHEN
                COALESCE(
                    plan_dep,
                    act_dep
                ) = board_time
            THEN 1
            END
        ) AS boards,
        COUNT(
            CASE
            WHEN
                COALESCE(
                    plan_arr,
                    act_arr
                ) = alight_time
            THEN 1
            END
        ) AS alights
    FROM (
        SELECT
            DATE_PART(
                'year',
                COALESCE(plan_arr, act_arr, plan_dep, act_dep)
            ) AS year,
            train_leg_id,
            train_station_id,
            plan_arr,
            act_arr,
            plan_dep,
            act_dep
        FROM train_station_leg_view
    ) train_station_leg_year_view
    INNER JOIN train_leg_high_view
    ON train_station_leg_year_view.train_leg_id
        = train_leg_high_view.train_leg_id
    GROUP BY year, train_station_id
)

$$;

CREATE FUNCTION select_transport_user_train_stats_years_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS transport_user_details_out_data
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
    )::transport_user_details_out_data;
END;
$$;
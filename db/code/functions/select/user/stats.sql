DROP FUNCTION IF EXISTS select_transport_user_train_leg_stats_by_user_id CASCADE;
DROP FUNCTION IF EXISTS select_transport_user_train_station_year_stats_by_user_id CASCADE;
DROP FUNCTION IF EXISTS select_transport_user_train_stats_numbers_by_user_id CASCADE;
DROP FUNCTION IF EXISTS select_transport_user_train_stats_years_by_user_id CASCADE;

CREATE FUNCTION select_transport_user_train_leg_stats_by_user_id (
    p_user_id INTEGER_NOTNULL
)
RETURNS transport_user_train_leg_overall_stats
LANGUAGE plpgsql
AS
$$
DECLARE
    v_train_leg_overall_stats transport_user_details_train_leg_out_data;
    v_train_leg_year_stats transport_user_details_train_leg_year_out_data[];
BEGIN
    CREATE TEMP TABLE transport_user_train_leg_stat AS
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
    WHERE user_id = p_user_id;

    CREATE TEMP TABLE transport_user_train_leg_distance_stat AS
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
    ) WHERE rownum = 1;

    CREATE TEMP TABLE transport_user_train_leg_duration_stat AS
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
    ) WHERE rownum = 1;

    CREATE TEMP TABLE transport_user_train_leg_delay_stat AS
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
    ) WHERE rownum = 1;

    SELECT INTO v_train_leg_overall_stats
        transport_user_train_leg_stats_view.count::BIGINT_NOTNULL,
        transport_user_train_leg_stats_view.total_distance::DECIMAL_NOTNULL,
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
        transport_user_train_leg_stats_view.total_duration::INTERVAL_NOTNULL,
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
        transport_user_train_leg_stats_view.total_delay::INTEGER,
        CASE
            WHEN transport_user_train_leg_delay_stat_longest.delay IS NULL
            THEN NULL
            ELSE (
                transport_user_train_leg_delay_stat_longest.delay,
                transport_user_train_leg_delay_stat_longest.train_leg_id,
                transport_user_train_leg_delay_stat_longest.description,
                transport_user_train_leg_delay_stat_longest.start_datetime
            )::transport_user_details_integer_timestamp_stat
        END AS longest_delay,
        CASE
            WHEN transport_user_train_leg_delay_stat_shortest.delay IS NULL
            THEN NULL
            ELSE (
                transport_user_train_leg_delay_stat_shortest.delay,
                transport_user_train_leg_delay_stat_shortest.train_leg_id,
                transport_user_train_leg_delay_stat_shortest.description,
                transport_user_train_leg_delay_stat_shortest.start_datetime
            )::transport_user_details_integer_timestamp_stat
        END AS shortest_delay
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
        = transport_user_train_leg_delay_stat_shortest.delay;

    SELECT INTO v_train_leg_year_stats
        ARRAY_AGG(
            (
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
            )::transport_user_details_train_leg_year_out_data
            ORDER BY year ASC
        )
    FROM (
        SELECT
            transport_user_train_leg_stats_view.year::INTEGER,
            transport_user_train_leg_stats_view.count::BIGINT_NOTNULL,
            transport_user_train_leg_stats_view.total_distance::DECIMAL_NOTNULL,
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
            transport_user_train_leg_stats_view.total_duration::INTERVAL_NOTNULL,
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
            transport_user_train_leg_stats_view.total_delay::INTEGER,
            CASE
                WHEN transport_user_train_leg_delay_stat_longest.delay IS NULL
                THEN NULL
                ELSE (
                    transport_user_train_leg_delay_stat_longest.delay,
                    transport_user_train_leg_delay_stat_longest.train_leg_id,
                    transport_user_train_leg_delay_stat_longest.description,
                    transport_user_train_leg_delay_stat_longest.start_datetime
                )::transport_user_details_integer_timestamp_stat
            END AS longest_delay,
            CASE
                WHEN transport_user_train_leg_delay_stat_shortest.delay IS NULL
                THEN NULL
                ELSE (
                    transport_user_train_leg_delay_stat_shortest.delay,
                    transport_user_train_leg_delay_stat_shortest.train_leg_id,
                    transport_user_train_leg_delay_stat_shortest.description,
                    transport_user_train_leg_delay_stat_shortest.start_datetime
                )::transport_user_details_integer_timestamp_stat
            END AS shortest_delay
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
        LEFT JOIN transport_user_train_leg_delay_stat
            transport_user_train_leg_delay_stat_longest
        ON transport_user_train_leg_stats_view.longest_delay
            = transport_user_train_leg_delay_stat_longest.delay
        AND transport_user_train_leg_stats_view.year
            = transport_user_train_leg_delay_stat_longest.year
        LEFT JOIN transport_user_train_leg_delay_stat
            transport_user_train_leg_delay_stat_shortest
        ON transport_user_train_leg_stats_view.shortest_delay
            = transport_user_train_leg_delay_stat_shortest.delay
        AND transport_user_train_leg_stats_view.year
            = transport_user_train_leg_delay_stat_shortest.year
    );

    DROP TABLE transport_user_train_leg_stat;
    DROP TABLE transport_user_train_leg_distance_stat;
    DROP TABLE transport_user_train_leg_duration_stat;
    DROP TABLE transport_user_train_leg_delay_stat;

    RETURN (
        v_train_leg_overall_stats,
        v_train_leg_year_stats
    )::transport_user_train_leg_overall_stats;
END;
$$;

CREATE FUNCTION select_transport_user_train_station_stats_by_user_id (
    p_user_id INTEGER_NOTNULL
)
RETURNS transport_user_train_station_overall_stats
LANGUAGE plpgsql
AS
$$
DECLARE
    v_train_station_overall_stats transport_user_details_train_station_out_data;
    v_train_station_year_stats transport_user_details_train_station_year_out_data[];
BEGIN
    CREATE TEMP TABLE transport_user_train_station_leg_year_stat AS
    SELECT
        train_station_year_stat.year,
        train_station_year_stat.train_station_id,
        train_station.station_crs,
        train_station.station_name,
        train_station_year_stat.total,
        train_station_year_stat.boards,
        train_station_year_stat.last_board,
        train_station_year_stat.alights,
        train_station_year_stat.last_alight,
        train_station_year_stat.calls
    FROM (
        SELECT
            year,
            train_station_id,
            COUNT(*) AS total,
            COUNT(
                CASE
                WHEN COALESCE(plan_dep, act_dep) = board_time
                THEN 1
                END
            ) AS boards,
            MAX(
                CASE
                WHEN COALESCE(plan_dep, act_dep) = board_time
                THEN COALESCE(plan_dep, act_dep)
                ELSE NULL
                END
            ) AS last_board,
            COUNT(
                CASE
                WHEN COALESCE(plan_arr, act_arr) = alight_time
                THEN 1
                END
            ) AS alights,
            MAX(
                CASE
                WHEN COALESCE(plan_arr, act_arr) = alight_time
                THEN COALESCE(plan_arr, act_arr)
                ELSE NULL
                END
            ) AS last_alight,
            COUNT(
                CASE
                WHEN COALESCE(plan_arr, act_arr) != alight_time
                    AND COALESCE(plan_arr, act_arr) != board_time
                THEN 1
                END
            ) AS calls
        FROM (
            SELECT
                DATE_PART(
                    'year',
                    COALESCE(
                        train_station_leg_view.plan_arr,
                        train_station_leg_view.act_arr,
                        train_station_leg_view.plan_dep,
                        train_station_leg_view.act_dep
                    )
                ) AS year,
                transport_user_train_leg.user_id,
                train_station_leg_view.train_leg_id,
                train_station_leg_view.board_time,
                train_station_leg_view.alight_time,
                train_station_leg_view.train_station_id,
                train_station_leg_view.plan_arr,
                train_station_leg_view.act_arr,
                train_station_leg_view.plan_dep,
                train_station_leg_view.act_dep
            FROM train_station_leg_view
            INNER JOIN transport_user_train_leg
            ON train_station_leg_view.train_leg_id
                = transport_user_train_leg.train_leg_id
            WHERE transport_user_train_leg.user_id = p_user_id
        ) train_station_leg_year_view
        GROUP BY
            train_station_leg_year_view.year,
            train_station_leg_year_view.train_station_id
    ) train_station_year_stat
    INNER JOIN train_station
    ON train_station_year_stat.train_station_id
        = train_station.train_station_id;

    CREATE TEMP TABLE transport_user_train_station_board_year_stat AS
    SELECT
        year,
        boards,
        train_station_id,
        station_name,
        station_crs
    FROM (
        SELECT
            year,
            boards,
            train_station_id,
            station_name,
            station_crs,
            ROW_NUMBER() OVER (
                PARTITION BY year, boards
                ORDER BY COALESCE(last_board, last_alight)
            ) AS rownum
        FROM transport_user_train_station_leg_year_stat
    ) WHERE rownum = 1;

    CREATE TEMP TABLE transport_user_train_station_alight_year_stat AS
    SELECT
        year,
        alights,
        train_station_id,
        station_name,
        station_crs
    FROM (
        SELECT
            year,
            alights,
            train_station_id,
            station_name,
            station_crs,
            ROW_NUMBER() OVER (
                PARTITION BY year, alights
                ORDER BY COALESCE(last_alight, last_board)
            ) AS rownum
        FROM transport_user_train_station_leg_year_stat
    ) WHERE rownum = 1;

    CREATE TEMP TABLE transport_user_train_station_board_alight_year_stat AS
    SELECT
        year,
        boards_and_alights,
        train_station_id,
        station_name,
        station_crs
    FROM (
        SELECT
            year,
            boards + alights AS boards_and_alights,
            train_station_id,
            station_name,
            station_crs,
            ROW_NUMBER() OVER (
                PARTITION BY year, boards + alights
                ORDER BY COALESCE(last_board, last_alight)
            ) AS rownum
        FROM transport_user_train_station_leg_year_stat
    ) WHERE rownum = 1;

    CREATE TEMP TABLE transport_user_train_station_call_year_stat AS
    SELECT
        year,
        calls,
        train_station_id,
        station_name,
        station_crs
    FROM (
        SELECT
            year,
            calls,
            train_station_id,
            station_name,
            station_crs,
            ROW_NUMBER() OVER (
                PARTITION BY year, calls
                ORDER BY COALESCE(last_board, last_alight)
            ) AS rownum
        FROM transport_user_train_station_leg_year_stat
    ) WHERE rownum = 1;

    CREATE TEMP TABLE transport_user_train_station_leg_stat AS
    SELECT
        train_station_stat.train_station_id,
        train_station.station_crs,
        train_station.station_name,
        train_station_stat.total,
        train_station_stat.boards,
        train_station_stat.last_board,
        train_station_stat.alights,
        train_station_stat.last_alight,
        train_station_stat.calls
    FROM (
        SELECT
            train_station_id,
            COUNT(*) AS total,
            COUNT(
                CASE
                WHEN COALESCE(plan_dep, act_dep) = board_time
                THEN 1
                END
            ) AS boards,
            MAX(
                CASE
                WHEN COALESCE(plan_dep, act_dep) = board_time
                THEN COALESCE(plan_dep, act_dep)
                ELSE NULL
                END
            ) AS last_board,
            COUNT(
                CASE
                WHEN COALESCE(plan_arr, act_arr) = alight_time
                THEN 1
                END
            ) AS alights,
            MAX(
                CASE
                WHEN COALESCE(plan_arr, act_arr) = alight_time
                THEN COALESCE(plan_arr, act_arr)
                ELSE NULL
                END
            ) AS last_alight,
            COUNT(
                CASE
                WHEN COALESCE(plan_arr, act_arr) != alight_time
                    AND COALESCE(plan_arr, act_arr) != board_time
                THEN 1
                END
            ) AS calls
        FROM (
            SELECT
                transport_user_train_leg.user_id,
                train_station_leg_view.train_leg_id,
                train_station_leg_view.board_time,
                train_station_leg_view.alight_time,
                train_station_leg_view.train_station_id,
                train_station_leg_view.plan_arr,
                train_station_leg_view.act_arr,
                train_station_leg_view.plan_dep,
                train_station_leg_view.act_dep
            FROM train_station_leg_view
            INNER JOIN transport_user_train_leg
            ON train_station_leg_view.train_leg_id
                = transport_user_train_leg.train_leg_id
            WHERE transport_user_train_leg.user_id = p_user_id
        ) transport_user_train_station_leg_view
        GROUP BY
            transport_user_train_station_leg_view.train_station_id
    ) train_station_stat
    INNER JOIN train_station
    ON train_station_stat.train_station_id
        = train_station.train_station_id;

    CREATE TEMP TABLE transport_user_train_station_board_stat AS
    SELECT
        boards,
        train_station_id,
        station_name,
        station_crs
    FROM (
        SELECT
            boards,
            train_station_id,
            station_name,
            station_crs,
            ROW_NUMBER() OVER (
                PARTITION BY boards
                ORDER BY COALESCE(last_board, last_alight)
            ) AS rownum
        FROM transport_user_train_station_leg_stat
    ) WHERE rownum = 1;

    CREATE TEMP TABLE transport_user_train_station_alight_stat AS
    SELECT
        alights,
        train_station_id,
        station_name,
        station_crs
    FROM (
        SELECT
            alights,
            train_station_id,
            station_name,
            station_crs,
            ROW_NUMBER() OVER (
                PARTITION BY alights
                ORDER BY COALESCE(last_alight, last_board)
            ) AS rownum
        FROM transport_user_train_station_leg_stat
    ) WHERE rownum = 1;

    CREATE TEMP TABLE transport_user_train_station_board_alight_stat AS
    SELECT
        boards_and_alights,
        train_station_id,
        station_name,
        station_crs
    FROM (
        SELECT
            boards + alights AS boards_and_alights,
            train_station_id,
            station_name,
            station_crs,
            ROW_NUMBER() OVER (
                PARTITION BY boards + alights
                ORDER BY COALESCE(last_board, last_alight)
            ) AS rownum
        FROM transport_user_train_station_leg_stat
    ) WHERE rownum = 1;

    CREATE TEMP TABLE transport_user_train_station_call_stat AS
    SELECT
        calls,
        train_station_id,
        station_name,
        station_crs
    FROM (
        SELECT
            calls,
            train_station_id,
            station_name,
            station_crs,
            ROW_NUMBER() OVER (
                PARTITION BY calls
                ORDER BY COALESCE(last_board, last_alight)
            ) AS rownum
        FROM transport_user_train_station_leg_stat
    ) WHERE rownum = 1;

    SELECT INTO v_train_station_overall_stats
        transport_user_train_station_leg_stat_number.station_count
            AS station_count,
        transport_user_train_station_leg_stat_number.station_count
            AS new_station_count,
        (
            transport_user_train_station_leg_stat_number.most_boards_and_alights,
            transport_user_train_station_board_alight_stat.train_station_id,
            transport_user_train_station_board_alight_stat.station_name
        )::transport_user_details_integer_stat
        AS most_boards_and_alights,
        (
            transport_user_train_station_leg_stat_number.most_boards,
            transport_user_train_station_board_stat.train_station_id,
            transport_user_train_station_board_stat.station_name
        )::transport_user_details_integer_stat
        AS most_boards,
        (
            transport_user_train_station_leg_stat_number.most_alights,
            transport_user_train_station_alight_stat.train_station_id,
            transport_user_train_station_alight_stat.station_name
        )::transport_user_details_integer_stat
        AS most_alights,
        CASE
            WHEN transport_user_train_station_leg_stat_number.most_calls = 0
            THEN NULL
            ELSE (
                transport_user_train_station_leg_stat_number.most_calls,
                transport_user_train_station_call_stat.train_station_id,
                transport_user_train_station_call_stat.station_name
            )::transport_user_details_integer_stat
        END
        AS most_calls
    FROM (
        SELECT
            COUNT(*) AS station_count,
            MAX(transport_user_train_station_leg_stat.boards) AS most_boards,
            MAX(transport_user_train_station_leg_stat.alights) AS most_alights,
            MAX(
                transport_user_train_station_leg_stat.boards
                    + transport_user_train_station_leg_stat.alights
            ) AS most_boards_and_alights,
            MAX(transport_user_train_station_leg_stat.calls) AS most_calls
        FROM transport_user_train_station_leg_stat
    ) transport_user_train_station_leg_stat_number
    INNER JOIN transport_user_train_station_board_alight_stat
    ON transport_user_train_station_leg_stat_number.most_boards_and_alights
        = transport_user_train_station_board_alight_stat.boards_and_alights
    INNER JOIN transport_user_train_station_board_stat
    ON transport_user_train_station_leg_stat_number.most_boards
        = transport_user_train_station_board_stat.boards
    INNER JOIN transport_user_train_station_alight_stat
    ON transport_user_train_station_leg_stat_number.most_alights
        = transport_user_train_station_alight_stat.alights
    INNER JOIN transport_user_train_station_call_stat
    ON transport_user_train_station_leg_stat_number.most_calls
        = transport_user_train_station_call_stat.calls;

    SELECT INTO v_train_station_year_stats
        ARRAY_AGG(
            (
                year,
                station_count::BIGINT_NOTNULL,
                new_station_count::BIGINT_NOTNULL,
                most_boards_and_alights,
                most_boards,
                most_alights,
                most_calls
            )::transport_user_details_train_station_year_out_data
            ORDER BY year ASC
        )
    FROM (
        SELECT
            train_station_leg_year_stat_number.year::INTEGER,
            train_station_leg_year_stat_number.station_count::BIGINT_NOTNULL,
            train_station_leg_year_stat_number.new_station_count::BIGINT_NOTNULL,
            (
                train_station_leg_year_stat_number.most_boards_and_alights,
                transport_user_train_station_board_alight_year_stat.train_station_id,
                transport_user_train_station_board_alight_year_stat.station_name
            )::transport_user_details_integer_stat
            AS most_boards_and_alights,
            (
                train_station_leg_year_stat_number.most_boards,
                transport_user_train_station_board_year_stat.train_station_id,
                transport_user_train_station_board_year_stat.station_name
            )::transport_user_details_integer_stat
            AS most_boards,
            (
                train_station_leg_year_stat_number.most_alights,
                transport_user_train_station_alight_year_stat.train_station_id,
                transport_user_train_station_alight_year_stat.station_name
            )::transport_user_details_integer_stat
            AS most_alights,
            CASE
                WHEN train_station_leg_year_stat_number.most_calls = 0
                THEN NULL
                ELSE (
                    train_station_leg_year_stat_number.most_calls,
                    transport_user_train_station_call_year_stat.train_station_id,
                    transport_user_train_station_call_year_stat.station_name
                )::transport_user_details_integer_stat
            END
            AS most_calls
        FROM (
            SELECT
                year,
                COUNT(
                    CASE
                    WHEN
                        transport_user_train_station_leg_year_stat.boards
                            + transport_user_train_station_leg_year_stat.alights
                            > 0
                    THEN 1
                    END
                ) AS station_count,
                COUNT(
                    CASE
                    WHEN transport_user_train_station_leg_year_stat.year
                        = train_station_year_first_visited.first_year_visited
                        AND transport_user_train_station_leg_year_stat.boards
                            + transport_user_train_station_leg_year_stat.alights
                            > 0
                    THEN 1
                    END
                ) AS new_station_count,
                MAX(transport_user_train_station_leg_year_stat.boards) AS most_boards,
                MAX(transport_user_train_station_leg_year_stat.alights) AS most_alights,
                MAX(
                    transport_user_train_station_leg_year_stat.boards
                        + transport_user_train_station_leg_year_stat.alights
                ) AS most_boards_and_alights,
                MAX(transport_user_train_station_leg_year_stat.calls) AS most_calls
            FROM transport_user_train_station_leg_year_stat
            INNER JOIN (
                SELECT
                    train_station_id,
                    MIN(year) AS first_year_visited
                FROM transport_user_train_station_leg_year_stat
                WHERE boards > 0 OR alights > 0
                GROUP BY train_station_id
            ) train_station_year_first_visited
            ON transport_user_train_station_leg_year_stat.train_station_id
                = train_station_year_first_visited.train_station_id
            GROUP BY year
        ) train_station_leg_year_stat_number
        INNER JOIN transport_user_train_station_board_alight_year_stat
        ON train_station_leg_year_stat_number.year
            = transport_user_train_station_board_alight_year_stat.year
        AND train_station_leg_year_stat_number.most_boards_and_alights
            = transport_user_train_station_board_alight_year_stat.boards_and_alights
        INNER JOIN transport_user_train_station_board_year_stat
        ON train_station_leg_year_stat_number.year
            = transport_user_train_station_board_year_stat.year
        AND train_station_leg_year_stat_number.most_boards
            = transport_user_train_station_board_year_stat.boards
        INNER JOIN transport_user_train_station_alight_year_stat
        ON train_station_leg_year_stat_number.year
            = transport_user_train_station_alight_year_stat.year
        AND train_station_leg_year_stat_number.most_alights
            = transport_user_train_station_alight_year_stat.alights
        INNER JOIN transport_user_train_station_call_year_stat
        ON train_station_leg_year_stat_number.year
            = transport_user_train_station_call_year_stat.year
        AND train_station_leg_year_stat_number.most_calls
            = transport_user_train_station_call_year_stat.calls
    );

    DROP TABLE transport_user_train_station_leg_year_stat;
    DROP TABLE transport_user_train_station_board_year_stat;
    DROP TABLE transport_user_train_station_alight_year_stat;
    DROP TABLE transport_user_train_station_board_alight_year_stat;
    DROP TABLE transport_user_train_station_call_year_stat;
    DROP TABLE transport_user_train_station_leg_stat;
    DROP TABLE transport_user_train_station_board_stat;
    DROP TABLE transport_user_train_station_alight_stat;
    DROP TABLE transport_user_train_station_board_alight_stat;
    DROP TABLE transport_user_train_station_call_stat;

    RETURN (
        v_train_station_overall_stats,
        v_train_station_year_stats
    )::transport_user_train_station_overall_stats;
END;
$$;

CREATE FUNCTION select_transport_user_train_stats_by_user_id (
    p_user_id INTEGER_NOTNULL
)
RETURNS transport_user_details_train_year_out_data
LANGUAGE plpgsql
AS
$$
DECLARE
    v_train_leg_stats transport_user_train_leg_overall_stats;
    v_train_station_stats transport_user_train_station_overall_stats;
    v_train_operator_stats transport_user_details_train_operator_out_data;
    v_train_class_stats transport_user_details_train_class_out_data;
    v_train_unit_stats transport_user_details_train_unit_out_data;
BEGIN
    v_train_leg_stats :=
        select_transport_user_train_leg_stats_by_user_id(p_user_id);
    v_train_station_stats :=
        select_transport_user_train_station_stats_by_user_id(p_user_id);
    RETURN (
        (v_train_leg_stats).overall_leg_stats,
        (v_train_leg_stats).year_leg_stats,
        (v_train_station_stats).overall_station_stats,
        (v_train_station_stats).year_station_stats
    )::transport_user_details_train_year_out_data;
END;
$$;

CREATE OR REPLACE FUNCTION select_transport_user_details (
    p_user_id INTEGER_NOTNULL
)
RETURNS transport_user_details_out_data
LANGUAGE plpgsql
AS
$$
DECLARE
    v_user_name TEXT;
    v_display_name TEXT;
    v_train_stats transport_user_details_train_year_out_data;
BEGIN
    SELECT
        user_name,
        display_name
    INTO
        v_user_name,
        v_display_name
    FROM
        transport_user;

    v_train_stats :=
        select_transport_user_train_stats_by_user_id(p_user_id);

    RETURN (
        p_user_id,
        v_user_name,
        v_display_name,
        v_train_stats
    )::transport_user_details_out_data;
END;
$$;

-- TODO
-- station stats numbers are wrong?
-- operator stats
-- unit stats
-- class stats
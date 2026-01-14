DROP FUNCTION IF EXISTS select_longest_distance_transport_user_train_legs_by_user_id CASCADE;
DROP FUNCTION IF EXISTS select_shortest_distance_transport_user_train_legs_by_user_id CASCADE;
DROP FUNCTION IF EXISTS select_longest_duration_transport_user_train_legs_by_user_id CASCADE;
DROP FUNCTION IF EXISTS select_shortest_duration_transport_user_train_legs_by_user_id CASCADE;
DROP FUNCTION IF EXISTS select_longest_delay_transport_user_train_legs_by_user_id CASCADE;
DROP FUNCTION IF EXISTS select_shortest_delay_transport_user_train_legs_by_user_id CASCADE;
DROP FUNCTION IF EXISTS select_transport_user_train_leg_stats_numbers_by_user_id CASCADE;
DROP FUNCTION IF EXISTS select_transport_user_train_leg_stats_by_user_id CASCADE;
DROP FUNCTION IF EXISTS select_transport_user_train_legs_by_user_id CASCADE;
DROP FUNCTION IF EXISTS select_longest_transport_user_train_legs_by_user_id CASCADE;
DROP FUNCTION IF EXISTS select_shortest_transport_user_train_legs_by_user_id CASCADE;

CREATE FUNCTION select_longest_distance_transport_user_train_legs_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE,
    p_rows_to_return INTEGER
)
RETURNS SETOF transport_user_train_leg_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_id,
    board_station,
    alight_station,
    start_datetime,
    operator,
    brand,
    distance,
    duration,
    delay
FROM (
    SELECT * FROM transport_user_train_leg_view
    WHERE user_id = p_user_id
    AND (p_search_start IS NULL OR start_datetime >= p_search_start)
    AND (p_search_end IS NULL OR start_datetime < p_search_end)
    ORDER BY
        transport_user_train_leg_view.distance DESC,
        transport_user_train_leg_view.start_datetime ASC
    LIMIT p_rows_to_return
);
$$;

CREATE FUNCTION select_shortest_distance_transport_user_train_legs_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE,
    p_rows_to_return INTEGER
)
RETURNS SETOF transport_user_train_leg_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_id,
    board_station,
    alight_station,
    start_datetime,
    operator,
    brand,
    distance,
    duration,
    delay
FROM (
    SELECT * FROM transport_user_train_leg_view
    WHERE user_id = p_user_id
    AND (p_search_start IS NULL OR start_datetime >= p_search_start)
    AND (p_search_end IS NULL OR start_datetime < p_search_end)
    ORDER BY
        transport_user_train_leg_view.distance ASC,
        transport_user_train_leg_view.start_datetime ASC
    LIMIT p_rows_to_return
);
$$;

CREATE FUNCTION select_longest_duration_transport_user_train_legs_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE,
    p_rows_to_return INTEGER
)
RETURNS SETOF transport_user_train_leg_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_id,
    board_station,
    alight_station,
    start_datetime,
    operator,
    brand,
    distance,
    duration,
    delay
FROM (
    SELECT * FROM transport_user_train_leg_view
    WHERE user_id = p_user_id
    AND (p_search_start IS NULL OR start_datetime >= p_search_start)
    AND (p_search_end IS NULL OR start_datetime < p_search_end)
    ORDER BY
        transport_user_train_leg_view.duration DESC,
        transport_user_train_leg_view.start_datetime ASC
    LIMIT p_rows_to_return
);
$$;

CREATE FUNCTION select_shortest_duration_transport_user_train_legs_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE,
    p_rows_to_return INTEGER
)
RETURNS SETOF transport_user_train_leg_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_id,
    board_station,
    alight_station,
    start_datetime,
    operator,
    brand,
    distance,
    duration,
    delay
FROM (
    SELECT * FROM transport_user_train_leg_view
    WHERE user_id = p_user_id
    AND (p_search_start IS NULL OR start_datetime >= p_search_start)
    AND (p_search_end IS NULL OR start_datetime < p_search_end)
    ORDER BY
        transport_user_train_leg_view.duration ASC,
        transport_user_train_leg_view.start_datetime ASC
    LIMIT p_rows_to_return
);
$$;

CREATE FUNCTION select_longest_delay_transport_user_train_legs_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE,
    p_rows_to_return INTEGER
)
RETURNS SETOF transport_user_train_leg_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_id,
    board_station,
    alight_station,
    start_datetime,
    operator,
    brand,
    distance,
    duration,
    delay
FROM (
    SELECT * FROM transport_user_train_leg_view
    WHERE user_id = p_user_id
    AND (p_search_start IS NULL OR start_datetime >= p_search_start)
    AND (p_search_end IS NULL OR start_datetime < p_search_end)
    ORDER BY
        transport_user_train_leg_view.delay DESC,
        transport_user_train_leg_view.start_datetime ASC
    LIMIT p_rows_to_return
);
$$;

CREATE FUNCTION select_shortest_delay_transport_user_train_legs_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE,
    p_rows_to_return INTEGER
)
RETURNS SETOF transport_user_train_leg_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_id,
    board_station,
    alight_station,
    start_datetime,
    operator,
    brand,
    distance,
    duration,
    delay
FROM (
    SELECT * FROM transport_user_train_leg_view
    WHERE user_id = p_user_id
    AND (p_search_start IS NULL OR start_datetime >= p_search_start)
    AND (p_search_end IS NULL OR start_datetime < p_search_end)
    ORDER BY
        transport_user_train_leg_view.delay ASC,
        transport_user_train_leg_view.start_datetime ASC
    LIMIT p_rows_to_return
);
$$;

CREATE FUNCTION select_transport_user_train_leg_stats_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE,
    p_rows_to_return INTEGER
)
RETURNS SETOF transport_user_train_leg_stats
LANGUAGE sql
AS
$$
WITH
transport_user_train_leg_longest_distance_view AS (
    SELECT
        ARRAY_AGG(
            (
                train_leg_id,
                board_station,
                alight_station,
                start_datetime,
                operator,
                brand,
                distance,
                duration,
                delay
            )::transport_user_train_leg_out_data
        ) AS legs
    FROM (
        SELECT * FROM transport_user_train_leg_view
        WHERE user_id = p_user_id
        AND (p_search_start IS NULL OR start_datetime >= p_search_start)
        AND (p_search_end IS NULL OR start_datetime < p_search_end)
        ORDER BY transport_user_train_leg_view.distance DESC
        LIMIT p_rows_to_return
    )
),
transport_user_train_leg_shortest_distance_view AS (
    SELECT
        ARRAY_AGG(
            (
                train_leg_id,
                board_station,
                alight_station,
                start_datetime,
                operator,
                brand,
                distance,
                duration,
                delay
            )::transport_user_train_leg_out_data
        ) AS legs
    FROM (
        SELECT * FROM transport_user_train_leg_view
        WHERE user_id = p_user_id
        AND (p_search_start IS NULL OR start_datetime >= p_search_start)
        AND (p_search_end IS NULL OR start_datetime < p_search_end)
        ORDER BY transport_user_train_leg_view.distance ASC
        LIMIT p_rows_to_return
    )
),
transport_user_train_leg_longest_duration_view AS (
    SELECT
        ARRAY_AGG(
            (
                train_leg_id,
                board_station,
                alight_station,
                start_datetime,
                operator,
                brand,
                distance,
                duration,
                delay
            )::transport_user_train_leg_out_data
        ) AS legs
    FROM (
        SELECT * FROM transport_user_train_leg_view
        WHERE user_id = p_user_id
        AND (p_search_start IS NULL OR start_datetime >= p_search_start)
        AND (p_search_end IS NULL OR start_datetime < p_search_end)
        ORDER BY transport_user_train_leg_view.duration DESC
        LIMIT p_rows_to_return
    )
),
transport_user_train_leg_shortest_duration_view AS (
    SELECT
        ARRAY_AGG(
            (
                train_leg_id,
                board_station,
                alight_station,
                start_datetime,
                operator,
                brand,
                distance,
                duration,
                delay
            )::transport_user_train_leg_out_data
        ) AS legs
    FROM (
        SELECT * FROM transport_user_train_leg_view
        WHERE user_id = p_user_id
        AND (p_search_start IS NULL OR start_datetime >= p_search_start)
        AND (p_search_end IS NULL OR start_datetime < p_search_end)
        ORDER BY transport_user_train_leg_view.duration ASC
        LIMIT p_rows_to_return
    )
),
transport_user_train_leg_longest_delay_view AS (
    SELECT
        ARRAY_AGG(
            (
                train_leg_id,
                board_station,
                alight_station,
                start_datetime,
                operator,
                brand,
                distance,
                duration,
                delay
            )::transport_user_train_leg_out_data
        ) AS legs
    FROM (
        SELECT * FROM transport_user_train_leg_view
        WHERE user_id = p_user_id
        AND (p_search_start IS NULL OR start_datetime >= p_search_start)
        AND (p_search_end IS NULL OR start_datetime < p_search_end)
        ORDER BY transport_user_train_leg_view.delay DESC
        LIMIT p_rows_to_return
    )
),
transport_user_train_leg_shortest_delay_view AS (
    SELECT
        ARRAY_AGG(
            (
                train_leg_id,
                board_station,
                alight_station,
                start_datetime,
                operator,
                brand,
                distance,
                duration,
                delay
            )::transport_user_train_leg_out_data
        ) AS legs
    FROM (
        SELECT * FROM transport_user_train_leg_view
        WHERE user_id = p_user_id
        AND (p_search_start IS NULL OR start_datetime >= p_search_start)
        AND (p_search_end IS NULL OR start_datetime < p_search_end)
        ORDER BY transport_user_train_leg_view.delay ASC
        LIMIT p_rows_to_return
    )
)
SELECT
    count,
    total_distance,
    longest_distance,
    longest_distance_leg.legs AS longest_distance_legs,
    shortest_distance,
    shortest_distance_leg.legs AS shortest_distance_legs,
    total_duration,
    longest_duration,
    longest_duration_leg.legs AS longest_duration_legs,
    shortest_duration,
    shortest_duration_leg.legs AS shortest_duration_legs,
    total_delay,
    longest_delay,
    longest_delay_leg.legs AS longest_delay_legs,
    shortest_delay,
    shortest_delay_leg.legs AS shortest_delay_legs
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
    FROM transport_user_train_leg_view
    WHERE user_id = p_user_id
    AND (p_search_start IS NULL OR start_datetime >= p_search_start)
    AND (p_search_end IS NULL OR start_datetime < p_search_end)
) train_leg_stat
CROSS JOIN transport_user_train_leg_longest_distance_view longest_distance_leg
CROSS JOIN transport_user_train_leg_shortest_distance_view shortest_distance_leg
CROSS JOIN transport_user_train_leg_longest_duration_view longest_duration_leg
CROSS JOIN transport_user_train_leg_shortest_duration_view shortest_duration_leg
CROSS JOIN transport_user_train_leg_longest_delay_view longest_delay_leg
CROSS JOIN transport_user_train_leg_shortest_delay_view shortest_delay_leg;
$$;

CREATE FUNCTION select_transport_user_train_legs_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_train_leg_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_id,
    board_station,
    alight_station,
    start_datetime,
    operator,
    brand,
    distance,
    duration,
    delay
FROM transport_user_train_leg_view
WHERE user_id = p_user_id
AND (p_search_start IS NULL OR start_datetime >= p_search_start)
AND (p_search_end IS NULL OR start_datetime < p_search_end)
ORDER BY start_datetime ASC;
$$;

CREATE FUNCTION select_longest_transport_user_train_legs_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE,
    p_rows_to_return INTEGER
)
RETURNS SETOF transport_user_train_leg_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_id,
    board_station,
    alight_station,
    start_datetime,
    operator,
    brand,
    distance,
    duration,
    delay
FROM transport_user_train_leg_view
WHERE user_id = p_user_id
AND (p_search_start IS NULL OR start_datetime >= p_search_start)
AND (p_search_end IS NULL OR start_datetime < p_search_end)
ORDER BY distance DESC
LIMIT p_rows_to_return;
$$;

CREATE FUNCTION select_shortest_transport_user_train_legs_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE,
    p_rows_to_return INTEGER
)
RETURNS SETOF transport_user_train_leg_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_id,
    board_station,
    alight_station,
    start_datetime,
    operator,
    brand,
    distance,
    duration,
    delay
FROM transport_user_train_leg_view
WHERE user_id = p_user_id
AND (p_search_start IS NULL OR start_datetime >= p_search_start)
AND (p_search_end IS NULL OR start_datetime < p_search_end)
ORDER BY distance ASC
LIMIT p_rows_to_return;
$$;

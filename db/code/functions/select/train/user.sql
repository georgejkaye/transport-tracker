DROP FUNCTION IF EXISTS select_transport_user_train_legs_by_user_id;
DROP FUNCTION IF EXISTS select_transport_user_train_stations_by_user_id;
DROP FUNCTION IF EXISTS select_transport_user_train_operator_by_user_id;

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
    origin,
    destination,
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

CREATE FUNCTION select_transport_user_train_stations_by_user_id (
    p_user_id INTEGER_NOTNULL
)
RETURNS SETOF transport_user_train_station_out_data
LANGUAGE sql
AS
$$
SELECT
    train_station_id,
    station_crs,
    station_name,
    station_operator,
    station_brand,
    boards,
    alights,
    calls,
    station_legs
FROM transport_user_train_station_view
WHERE user_id = p_user_id
ORDER BY station_name ASC;
$$;

CREATE FUNCTION select_transport_user_train_station_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_train_station_id INTEGER_NOTNULL
)
RETURNS SETOF transport_user_train_station_out_data
LANGUAGE sql
AS
$$
SELECT
    train_station_id,
    station_crs,
    station_name,
    station_operator,
    station_brand,
    boards,
    alights,
    calls,
    station_legs
FROM transport_user_train_station_view
WHERE user_id = p_user_id
AND train_station_id = p_train_station_id
ORDER BY station_name ASC;
$$;

CREATE FUNCTION select_transport_user_train_station_by_user_id_and_station_crs (
    p_user_id INTEGER_NOTNULL,
    p_station_crs TEXT_NOTNULL
)
RETURNS SETOF transport_user_train_station_out_data
LANGUAGE sql
AS
$$
SELECT
    train_station_id,
    station_crs,
    station_name,
    station_operator,
    station_brand,
    boards,
    alights,
    calls,
    station_legs
FROM transport_user_train_station_view
WHERE user_id = p_user_id
AND station_crs = p_station_crs
ORDER BY station_name ASC;
$$;

CREATE FUNCTION select_transport_user_train_stock_class_by_user_id_and_class (
    p_user_id INTEGER_NOTNULL,
    p_stock_class INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_train_class_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_class_stock.stock_class,
    train_stock.name,
    train_leg_class_stock.count,
    train_leg_class_stock.distance,
    train_leg_class_stock.duration,
    train_leg_class_stock.legs
FROM (
    SELECT
        train_leg_stock_class_view.stock_class,
        COUNT(train_leg_stock_class_view.*) AS count,
        SUM(train_leg_stock_class_view.distance) AS distance,
        SUM(train_leg_stock_class_view.duration) AS duration,
        ARRAY_AGG(
            (
                train_leg_high_view.train_leg_id,
                train_leg_high_view.leg_start_time,
                train_leg_high_view.origin,
                train_leg_high_view.destination,
                train_leg_high_view.operator,
                train_leg_high_view.brand,
                train_leg_stock_class_view.units,
                train_leg_stock_class_view.distance,
                train_leg_stock_class_view.duration
            )::transport_user_train_class_leg_out_data
        ) AS legs
    FROM train_leg_stock_class_view
    INNER JOIN train_leg_high_view
    ON train_leg_stock_class_view.train_leg_id
        = train_leg_high_view.train_leg_id
    INNER JOIN transport_user_train_leg
    ON train_leg_stock_class_view.train_leg_id
        = transport_user_train_leg.train_leg_id
    WHERE transport_user_train_leg.user_id = p_user_id
    AND (
        p_search_start IS NULL
        OR train_leg_high_view.leg_start_time >= p_search_start
    )
    AND (
        p_search_end IS NULL
        OR train_leg_high_view.leg_start_time < p_search_end
    )
    GROUP BY
        user_id,
        train_leg_stock_class_view.stock_class
) train_leg_class_stock
INNER JOIN train_stock
ON train_leg_class_stock.stock_class = train_stock.stock_class
WHERE train_leg_class_stock.stock_class = p_stock_class;
$$;

CREATE FUNCTION select_transport_user_train_stock_class_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_train_class_high_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_class_stock.stock_class,
    train_stock.name,
    train_leg_class_stock.count,
    train_leg_class_stock.distance,
    train_leg_class_stock.duration
FROM (
    SELECT
        train_leg_stock_class_stats_view.stock_class,
        COUNT(train_leg_stock_class_stats_view.*) AS count,
        SUM(train_leg_stock_class_stats_view.distance) AS distance,
        SUM(train_leg_stock_class_stats_view.duration) AS duration
    FROM train_leg_stock_class_stats_view
    INNER JOIN train_leg_high_view
    ON train_leg_stock_class_stats_view.train_leg_id
        = train_leg_high_view.train_leg_id
    INNER JOIN transport_user_train_leg
    ON train_leg_stock_class_stats_view.train_leg_id
        = transport_user_train_leg.train_leg_id
    WHERE transport_user_train_leg.user_id = p_user_id
    AND (
        p_search_start IS NULL
        OR train_leg_high_view.leg_start_time >= p_search_start
    )
    AND (
        p_search_end IS NULL
        OR train_leg_high_view.leg_start_time < p_search_end
    )
    GROUP BY
        user_id,
        train_leg_stock_class_stats_view.stock_class
) train_leg_class_stock
INNER JOIN train_stock
ON train_leg_class_stock.stock_class = train_stock.stock_class;
$$;

-- CREATE FUNCTION select_transport_user_train_stock_unit_by_user_id_and_number (
--     p_user_id INTEGER_NOTNULL,
--     p_stock_number INTEGER_NOTNULL,
--     p_search_start TIMESTAMP WITH TIME ZONE,
--     p_search_end TIMESTAMP WITH TIME ZONE
-- )
-- RETURNS SETOF transport_user_train_unit_out_data
-- LANGUAGE sql
-- AS
-- $$
-- SELECT
--     train_leg_stock_report_view.stock_number,
--     train_leg_stock_report_view.stock_class,
--     train_leg_stock_report_view.stock_subclass,
--     train_leg_stock_report_view.stock_cars,
--     COUNT(train_leg_stock_report_view.*) AS unit_count,
--     SUM(train_leg_stock_report_view.distance) AS distance,
--     SUM(train_leg_stock_report_view.duration) AS duration,
--     ARRAY_AGG((
--         train_leg_stock_report_view.train_leg_id,
--         train_leg_stock_report_view.leg_start_time,
--         train_leg_stock_report_view.stock_start_station,
--         train_leg_stock_report_view.stock_end_station,
--         train_leg_stock_report_view.distance,
--         train_leg_stock_report_view.duration,
--         train_leg_stock_report_view.leg_start_station,
--         train_leg_stock_report_view.leg_end_station,
--         train_leg_stock_report_view.operator,
--         train_leg_stock_report_view.brand
--     )::transport_user_train_unit_leg_out_data)
--     AS unit_legs
-- FROM train_leg_stock_report_view
-- INNER JOIN transport_user_train_leg
-- ON train_leg_stock_report_view.train_leg_id
--     = transport_user_train_leg.train_leg_id
-- WHERE transport_user_train_leg.user_id = p_user_id
-- AND train_leg_stock_report_view.stock_number = p_stock_number
-- AND (
--     p_search_start IS NULL
--     OR train_leg_stock_report_view.leg_start_time >= p_search_start
-- )
-- AND (
--     p_search_end IS NULL
--     OR train_leg_stock_report_view.leg_start_time < p_search_end
-- )
-- -- TODO: we can do this better with a proper stock unit table
-- GROUP BY
--     user_id,
--     train_leg_stock_report_view.stock_number,
--     train_leg_stock_report_view.stock_class,
--     train_leg_stock_report_view.stock_subclass,
--     train_leg_stock_report_view.stock_cars,
--     train_leg_stock_report_view.operator,
--     train_leg_stock_report_view.brand;
-- $$;

-- CREATE FUNCTION select_transport_user_train_stock_unit_by_user_id (
--     p_user_id INTEGER_NOTNULL,
--     p_search_start TIMESTAMP WITH TIME ZONE,
--     p_search_end TIMESTAMP WITH TIME ZONE
-- )
-- RETURNS SETOF transport_user_train_unit_high_out_data
-- LANGUAGE sql
-- AS
-- $$
-- SELECT
--     train_leg_stock_report_view.stock_number,
--     train_leg_stock_report_view.stock_class,
--     train_leg_stock_report_view.stock_subclass,
--     train_leg_stock_report_view.stock_cars,
--     COUNT(train_leg_stock_report_view.*) AS unit_count,
--     SUM(train_leg_stock_report_view.distance) AS distance,
--     SUM(train_leg_stock_report_view.duration) AS duration
-- FROM train_leg_stock_report_view
-- INNER JOIN transport_user_train_leg
-- ON train_leg_stock_report_view.train_leg_id
--     = transport_user_train_leg.train_leg_id
-- AND transport_user_train_leg.user_id = p_user_id
-- WHERE (
--     p_search_start IS NULL
--     OR train_leg_stock_report_view.leg_start_time >= p_search_start
-- )
-- AND (
--     p_search_end IS NULL
--     OR train_leg_stock_report_view.leg_start_time < p_search_end
-- )
-- AND train_leg_stock_report_view.stock_number IS NOT NULL
-- -- TODO: we can do this better with a proper stock unit table
-- GROUP BY
--     user_id,
--     train_leg_stock_report_view.stock_number,
--     train_leg_stock_report_view.stock_class,
--     train_leg_stock_report_view.stock_subclass,
--     train_leg_stock_report_view.stock_cars,
--     train_leg_stock_report_view.operator,
--     train_leg_stock_report_view.brand;
-- $$;

CREATE FUNCTION select_transport_user_train_operator_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_by_brands BOOLEAN_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_train_operator_high_out_data
LANGUAGE sql
AS
$$
SELECT
    operator_id,
    operator_code,
    operator_name,
    is_brand,
    leg_count,
    leg_duration,
    leg_distance,
    leg_delay
FROM (
    SELECT
        user_id,
        operator_id,
        operator_code,
        operator_name,
        FALSE as is_brand,
        leg_count,
        leg_duration,
        leg_distance,
        leg_delay,
        operator_brands
    FROM (
        SELECT
            transport_user_train_leg_view.user_id,
            (transport_user_train_leg_view.operator).operator_id,
            (transport_user_train_leg_view.operator).operator_code,
            (transport_user_train_leg_view.operator).operator_name,
            FALSE AS is_brand,
            COUNT(*) AS leg_count,
            SUM(
                COALESCE(transport_user_train_leg_view.duration, INTERVAL '0 days')
            ) AS leg_duration,
            SUM(
                COALESCE(transport_user_train_leg_view.distance, 0)
            ) AS leg_distance,
            SUM(
                COALESCE(transport_user_train_leg_view.delay, 0)
            ) AS leg_delay,
            operator_brands
        FROM transport_user_train_leg_view
        LEFT JOIN (
            SELECT
                train_operator_id,
                ARRAY_AGG(
                    (
                        train_brand_id,
                        brand_code,
                        brand_name
                    )::train_leg_operator_out_data
                ) AS operator_brands
            FROM train_brand
            GROUP BY train_operator_id
        ) train_operator_brand
        ON (transport_user_train_leg_view.operator).operator_id
        = train_operator_brand.train_operator_id
        WHERE (
            p_search_start IS NULL
            OR transport_user_train_leg_view.start_datetime >= p_search_start
        )
        AND (
            p_search_end IS NULL
            OR transport_user_train_leg_view.start_datetime < p_search_end
        )
        GROUP BY
            transport_user_train_leg_view.user_id,
            transport_user_train_leg_view.operator,
            train_operator_brand.operator_brands
    )
    UNION (
        SELECT
            user_id,
            operator_id,
            operator_code,
            operator_name,
            TRUE as is_brand,
            leg_count,
            leg_duration,
            leg_distance,
            leg_delay,
            ARRAY[]::train_leg_operator_out_data[] AS operator_brands
        FROM (
            SELECT
                transport_user_train_leg_view.user_id,
                (transport_user_train_leg_view.brand).operator_id,
                (transport_user_train_leg_view.brand).operator_code,
                (transport_user_train_leg_view.brand).operator_name,
                COUNT(*) AS leg_count,
                SUM(
                    COALESCE(transport_user_train_leg_view.duration, INTERVAL '0 days')
                ) AS leg_duration,
                SUM(
                    COALESCE(transport_user_train_leg_view.distance, 0)
                ) AS leg_distance,
                SUM(
                    COALESCE(transport_user_train_leg_view.delay, 0)
                ) AS leg_delay
            FROM transport_user_train_leg_view
            WHERE transport_user_train_leg_view.brand IS NOT NULL
            AND (
                p_search_start IS NULL
                OR transport_user_train_leg_view.start_datetime >= p_search_start
            )
            AND (
                p_search_end IS NULL
                OR transport_user_train_leg_view.start_datetime < p_search_end
            )
            GROUP BY
                transport_user_train_leg_view.user_id,
                transport_user_train_leg_view.brand
        )
    )
) transport_user_train_operator_brand
WHERE user_id = p_user_id
AND (
    (p_by_brands AND (is_brand OR operator_brands IS NULL))
    OR (NOT p_by_brands AND (NOT is_brand))
)
ORDER BY transport_user_train_operator_brand.operator_name ASC;
$$;

CREATE FUNCTION select_transport_user_train_operator_by_user_id_and_operator_id (
    p_user_id INTEGER_NOTNULL,
    p_operator_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_train_operator_out_data
LANGUAGE sql
AS
$$
SELECT
    operator_id,
    operator_code,
    operator_name,
    leg_count,
    leg_duration,
    leg_distance,
    leg_delay,
    operator_legs
FROM (
    SELECT
        transport_user_train_leg_view.user_id,
        (transport_user_train_leg_view.operator).operator_id,
        (transport_user_train_leg_view.operator).operator_code,
        (transport_user_train_leg_view.operator).operator_name,
        COUNT(*) AS leg_count,
        SUM(
            COALESCE(transport_user_train_leg_view.duration, INTERVAL '0 days')
        ) AS leg_duration,
        SUM(
            COALESCE(transport_user_train_leg_view.distance, 0)
        ) AS leg_distance,
        SUM(
            COALESCE(transport_user_train_leg_view.delay, 0)
        ) AS leg_delay,
        ARRAY_AGG(
            (
                transport_user_train_leg_view.train_leg_id,
                transport_user_train_leg_view.origin,
                transport_user_train_leg_view.destination,
                transport_user_train_leg_view.start_datetime,
                transport_user_train_leg_view.distance,
                transport_user_train_leg_view.duration,
                transport_user_train_leg_view.delay
            )::transport_user_train_operator_train_leg_out_data
        ) AS operator_legs,
        operator_brands
    FROM transport_user_train_leg_view
    LEFT JOIN (
        SELECT
            train_operator_id,
            ARRAY_AGG(
                (
                    train_brand_id,
                    brand_code,
                    brand_name
                )::train_leg_operator_out_data
            ) AS operator_brands
        FROM train_brand
        GROUP BY train_operator_id
    ) train_operator_brand
    ON (transport_user_train_leg_view.operator).operator_id
    = train_operator_brand.train_operator_id
    WHERE (
        p_search_start IS NULL
        OR transport_user_train_leg_view.start_datetime >= p_search_start
    )
    AND (
        p_search_end IS NULL
        OR transport_user_train_leg_view.start_datetime < p_search_end
    )
    GROUP BY
        transport_user_train_leg_view.user_id,
        transport_user_train_leg_view.operator,
        train_operator_brand.operator_brands
)
WHERE user_id = p_user_id
AND operator_id = p_operator_id
ORDER BY operator_name ASC;
$$;

CREATE FUNCTION select_transport_user_train_brand_by_user_id_and_brand_id (
    p_user_id INTEGER_NOTNULL,
    p_operator_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_train_operator_out_data
LANGUAGE sql
AS
$$
SELECT
    operator_id,
    operator_code,
    operator_name,
    leg_count,
    leg_duration,
    leg_distance,
    leg_delay,
    operator_legs
FROM (
    SELECT
        transport_user_train_leg_view.user_id,
        (transport_user_train_leg_view.brand).operator_id,
        (transport_user_train_leg_view.brand).operator_code,
        (transport_user_train_leg_view.brand).operator_name,
        COUNT(*) AS leg_count,
        SUM(
            COALESCE(transport_user_train_leg_view.duration, INTERVAL '0 days')
        ) AS leg_duration,
        SUM(
            COALESCE(transport_user_train_leg_view.distance, 0)
        ) AS leg_distance,
        SUM(
            COALESCE(transport_user_train_leg_view.delay, 0)
        ) AS leg_delay,
        ARRAY_AGG(
            (
                transport_user_train_leg_view.train_leg_id,
                transport_user_train_leg_view.origin,
                transport_user_train_leg_view.destination,
                transport_user_train_leg_view.start_datetime,
                transport_user_train_leg_view.distance,
                transport_user_train_leg_view.duration,
                transport_user_train_leg_view.delay
            )::transport_user_train_operator_train_leg_out_data
        ) AS operator_legs
    FROM transport_user_train_leg_view
    WHERE transport_user_train_leg_view.brand IS NOT NULL
    AND (
        p_search_start IS NULL
        OR transport_user_train_leg_view.start_datetime >= p_search_start
    )
    AND (
        p_search_end IS NULL
        OR transport_user_train_leg_view.start_datetime < p_search_end
    )
    GROUP BY
        transport_user_train_leg_view.user_id,
        transport_user_train_leg_view.brand
)
WHERE user_id = p_user_id
AND operator_id = p_operator_id
ORDER BY operator_name ASC;
$$;
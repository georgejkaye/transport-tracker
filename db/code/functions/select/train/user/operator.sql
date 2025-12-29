DROP FUNCTION IF EXISTS select_transport_user_train_operator_by_user_id;
DROP FUNCTION IF EXISTS select_transport_user_train_operator_by_user_id_and_operator_id;
DROP FUNCTION IF EXISTS select_transport_user_train_brand_by_user_id_and_brand_id;

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
                transport_user_train_leg_view.board_station,
                transport_user_train_leg_view.board_station_station,
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
                transport_user_train_leg_view.board_station,
                transport_user_train_leg_view.alight_station,
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
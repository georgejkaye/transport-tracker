DROP VIEW IF EXISTS transport_user_train_leg_view;
DROP VIEW IF EXISTS transport_user_train_station_view;
DROP VIEW IF EXISTS transport_user_train_class_view;
DROP VIEW IF EXISTS transport_user_train_class_high_view;
DROP VIEW IF EXISTS transport_user_train_operator_view;
DROP VIEW IF EXISTS transport_user_train_leg_distance_view;
DROP VIEW IF EXISTS transport_user_train_leg_duration_view;
DROP VIEW IF EXISTS transport_user_train_leg_delay_view;

CREATE VIEW transport_user_train_leg_view AS
SELECT
    transport_user_train_leg.user_id,
    train_leg.train_leg_id,
    (
        train_leg_start_station.train_station_id,
        train_leg_start_station.station_crs,
        train_leg_start_station.station_name
    )::train_station_high_out_data AS board_station,
    (
        train_leg_end_station.train_station_id,
        train_leg_end_station.station_crs,
        train_leg_end_station.station_name
    )::train_station_high_out_data AS alight_station,
    train_leg_boundary_time.board_time AS start_datetime,
    (
        train_operator.train_operator_id,
        train_operator.operator_code,
        train_operator.operator_name
    )::train_operator_high_out_data AS operator,
    CASE
        WHEN train_brand.train_brand_id IS NULL
        THEN NULL
        ELSE (
            train_brand.train_brand_id,
            train_brand.brand_code,
            train_brand.brand_name
        )::train_operator_high_out_data
    END AS brand,
    train_leg.distance,
    train_leg_boundary_time.leg_end_time
        - train_leg_boundary_time.board_time AS duration,
    EXTRACT(
        HOUR FROM train_leg_end_call.act_arr - train_leg_end_call.plan_arr) * 60
        + EXTRACT(
            MINUTE FROM train_leg_end_call.act_arr - train_leg_end_call.plan_arr
        ) AS delay
FROM transport_user_train_leg
INNER JOIN train_leg
ON transport_user_train_leg.train_leg_id = train_leg.train_leg_id
INNER JOIN (
    SELECT
        train_leg_call.train_leg_id,
        MIN(
            COALESCE(
                train_call.plan_dep,
                train_call.plan_arr,
                train_call.act_dep,
                train_call.act_arr
            )
        ) AS board_time,
        MAX(
            COALESCE(
                train_call.plan_arr,
                train_call.plan_dep,
                train_call.act_arr,
                train_call.act_dep
            )
        ) AS leg_end_time
    FROM train_leg_call
    INNER JOIN train_call
    ON train_leg_call.arr_call_id = train_call.train_call_id
    OR train_leg_call.dep_call_id = train_call.train_call_id
    GROUP BY train_leg_call.train_leg_id
) train_leg_boundary_time
ON train_leg.train_leg_id = train_leg_boundary_time.train_leg_id
INNER JOIN train_call train_leg_start_call
ON train_leg_boundary_time.board_time
    = COALESCE(
        train_leg_start_call.plan_dep,
        train_leg_start_call.plan_arr,
        train_leg_start_call.act_dep,
        train_leg_start_call.act_arr
    )
INNER JOIN train_station train_leg_start_station
ON train_leg_start_call.train_station_id
    = train_leg_start_station.train_station_id
INNER JOIN train_call train_leg_end_call
ON train_leg_boundary_time.leg_end_time
    = COALESCE(
        train_leg_end_call.plan_arr,
        train_leg_end_call.plan_dep,
        train_leg_end_call.act_arr,
        train_leg_end_call.act_dep
    )
INNER JOIN train_station train_leg_end_station
ON train_leg_end_call.train_station_id
    = train_leg_end_station.train_station_id
INNER JOIN train_service
ON train_leg_start_call.train_service_id = train_service.train_service_id
INNER JOIN train_operator
ON train_service.train_operator_id = train_operator.train_operator_id
LEFT JOIN train_brand
ON train_service.train_brand_id = train_brand.train_brand_id;

CREATE OR REPLACE VIEW train_station_leg_call_view AS
SELECT
    COALESCE(
        arr_train_call.train_station_id,
        dep_train_call.train_station_id
    ) AS train_station_id,
    train_leg_call.train_leg_id,
    train_leg_call.train_leg_call_id,
    arr_train_call.train_call_id AS arr_train_call_id,
    arr_train_call.plan_arr,
    arr_train_call.act_arr,
    dep_train_call.train_call_id AS dep_train_call_id,
    dep_train_call.plan_dep,
    dep_train_call.act_dep,
    COALESCE(
        arr_train_call.plan_arr,
        dep_train_call.plan_dep,
        arr_train_call.act_arr,
        dep_train_call.act_dep
    ) AS sort_call_time
FROM train_leg_call
LEFT JOIN train_call arr_train_call
ON train_leg_call.arr_call_id = arr_train_call.train_call_id
LEFT JOIN train_call dep_train_call
ON train_leg_call.dep_call_id = dep_train_call.train_call_id;

CREATE OR REPLACE VIEW train_station_leg_view AS
SELECT
    train_station_leg_call_view.train_station_id,
    train_station_leg_call_view.train_leg_id,
    train_leg_high_view.board_time,
    train_leg_high_view.alight_time,
    train_leg_high_view.board_station,
    train_leg_high_view.alight_station,
    train_station_leg_call_view.plan_arr,
    train_station_leg_call_view.act_arr,
    train_station_leg_call_view.plan_dep,
    train_station_leg_call_view.act_dep,
    train_leg_high_view.operator,
    train_leg_high_view.brand,
    train_station_leg_call_before.calls_before,
    train_station_leg_call_before.calls_before AS call_index,
    train_leg_high_view.total_calls
        - (train_station_leg_call_before.calls_before + 1) AS calls_after
FROM train_station_leg_call_view
INNER JOIN train_leg_high_view
ON train_station_leg_call_view.train_leg_id
    = train_leg_high_view.train_leg_id
LEFT JOIN train_call arr_train_call
ON train_station_leg_call_view.arr_train_call_id = arr_train_call.train_call_id
LEFT JOIN train_call dep_train_call
ON train_station_leg_call_view.dep_train_call_id = dep_train_call.train_call_id
LEFT JOIN (
    SELECT
        train_station_leg_call_view.train_station_id,
        train_station_leg_call_view.train_leg_id,
        COUNT(before_train_station_leg_call_view.*) - 1 AS calls_before
    FROM train_station_leg_call_view
    INNER JOIN train_station_leg_call_view before_train_station_leg_call_view
    ON train_station_leg_call_view.train_leg_id
        = before_train_station_leg_call_view.train_leg_id
    AND train_station_leg_call_view.sort_call_time
        >= before_train_station_leg_call_view.sort_call_time
    GROUP BY
        train_station_leg_call_view.train_station_id,
        train_station_leg_call_view.train_leg_id
) train_station_leg_call_before
ON train_station_leg_call_view.train_station_id
    = train_station_leg_call_before.train_station_id
AND train_station_leg_call_view.train_leg_id
    = train_station_leg_call_before.train_leg_id;

CREATE OR REPLACE VIEW transport_user_train_operator_view AS
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
    operator_legs,
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
                )::train_operator_high_out_data
            ) AS operator_brands
        FROM train_brand
        GROUP BY train_operator_id
    ) train_operator_brand
    ON (transport_user_train_leg_view.operator).operator_id
     = train_operator_brand.train_operator_id
    GROUP BY
        transport_user_train_leg_view.user_id,
        transport_user_train_leg_view.operator,
        train_operator_brand.operator_brands
)
UNION
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
    operator_legs,
    ARRAY[]::train_operator_high_out_data[] AS operator_brands
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
    GROUP BY
        transport_user_train_leg_view.user_id,
        transport_user_train_leg_view.brand
);

CREATE OR REPLACE VIEW transport_user_train_operator_high_view AS
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
                )::train_operator_high_out_data
            ) AS operator_brands
        FROM train_brand
        GROUP BY train_operator_id
    ) train_operator_brand
    ON (transport_user_train_leg_view.operator).operator_id
     = train_operator_brand.train_operator_id
    GROUP BY
        transport_user_train_leg_view.user_id,
        transport_user_train_leg_view.operator,
        train_operator_brand.operator_brands
)
UNION
SELECT
    user_id,
    operator_id,
    operator_code,
    operator_name,
    TRUE AS is_brand,
    leg_count,
    leg_duration,
    leg_distance,
    leg_delay,
    ARRAY[]::train_operator_high_out_data[] AS operator_brands
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
    GROUP BY
        transport_user_train_leg_view.user_id,
        transport_user_train_leg_view.brand
);
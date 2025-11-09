DROP VIEW IF EXISTS transport_user_train_leg_view;
DROP VIEW IF EXISTS transport_user_train_station_view;

CREATE VIEW transport_user_train_leg_view AS
SELECT
    transport_user_train_leg.user_id,
    train_leg.train_leg_id,
    (
        train_leg_start_station.train_station_id,
        train_leg_start_station.station_crs,
        train_leg_start_station.station_name
    )::transport_user_train_leg_station_out_data AS origin,
    (
        train_leg_end_station.train_station_id,
        train_leg_end_station.station_crs,
        train_leg_end_station.station_name
    )::transport_user_train_leg_station_out_data AS destination,
    train_leg_boundary_time.leg_start_time AS start_datetime,
    (
        train_operator.train_operator_id,
        train_operator.operator_code,
        train_operator.operator_name
    )::train_leg_operator_out_data AS operator,
    CASE
        WHEN train_brand.train_brand_id IS NULL
        THEN NULL
        ELSE (
            train_brand.train_brand_id,
            train_brand.brand_code,
            train_brand.brand_name
        )::train_leg_operator_out_data
    END AS brand,
    train_leg.distance,
    train_leg_boundary_time.leg_end_time
        - train_leg_boundary_time.leg_start_time AS duration,
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
        ) AS leg_start_time,
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
ON train_leg_boundary_time.leg_start_time
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

CREATE OR REPLACE VIEW transport_user_train_station_view AS
WITH
    train_leg_board_alight_time_view AS (
        SELECT
            train_leg_id,
            MIN(COALESCE(plan_arr, plan_dep, act_arr, act_dep)) AS board_time,
            MAX(COALESCE(plan_arr, plan_dep, act_arr, act_dep)) AS alight_time
        FROM train_leg_call
        INNER JOIN train_call
        ON train_leg_call.arr_call_id = train_call.train_call_id
        OR train_leg_call.dep_call_id = train_call.train_call_id
        GROUP BY train_leg_id
    ),
    train_station_leg_call_time_view AS (
        SELECT
            train_call.train_station_id,
            train_leg_call.train_leg_id,
            train_call.train_call_id,
            COALESCE(plan_arr, plan_dep, act_arr, act_dep) AS call_time
        FROM train_leg_call
        INNER JOIN train_call
        ON train_leg_call.arr_call_id = train_call.train_call_id
        OR train_leg_call.dep_call_id = train_call.train_call_id
    )
SELECT
    transport_user_train_station_leg_count_view.user_id,
    train_station.train_station_id,
    train_station.station_crs,
    train_station.station_name,
    (
        train_operator.train_operator_id,
        train_operator.operator_code,
        train_operator.operator_name
    )::transport_user_train_station_operator_out_data AS station_operator,
    CASE WHEN train_brand.train_brand_id IS NULL
    THEN
        NULL
    ELSE
        (
            train_brand.train_brand_id,
            train_brand.brand_code,
            train_brand.brand_name
        )::transport_user_train_station_operator_out_data
    END AS station_brand,
    transport_user_train_station_leg_count_view.boards,
    transport_user_train_station_leg_count_view.alights,
    transport_user_train_station_leg_count_view.calls
    -- train_station_leg.station_legs
FROM train_station
INNER JOIN train_operator
ON train_station.train_operator_id = train_operator.train_operator_id
LEFT JOIN train_brand
ON train_station.train_brand_id = train_brand.train_brand_id
INNER JOIN (
    SELECT
        transport_user_train_leg.user_id,
        train_station_id,
        COUNT(
            CASE WHEN
                call_time = board_time
            THEN 1
            END
        ) AS boards,
        COUNT(
            CASE WHEN
                call_time = alight_time
            THEN 1
            END
        ) AS alights,
        COUNT(
            CASE WHEN
                call_time NOT IN (board_time, alight_time)
            THEN 1
            END
        ) AS calls
    FROM transport_user_train_leg
    INNER JOIN train_station_leg_call_time_view
    ON transport_user_train_leg.train_leg_id
        = train_station_leg_call_time_view.train_leg_id
    INNER JOIN train_leg_board_alight_time_view
    ON train_station_leg_call_time_view.train_leg_id
        = train_leg_board_alight_time_view.train_leg_id
    GROUP BY user_id, train_station_id
) transport_user_train_station_leg_count_view
ON train_station.train_station_id
    = transport_user_train_station_leg_count_view.train_station_id;
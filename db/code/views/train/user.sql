DROP VIEW IF EXISTS transport_user_train_leg_high_view;
DROP VIEW IF EXISTS transport_user_train_station_view;
DROP VIEW IF EXISTS transport_user_train_class_view;

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
    train_leg_high_view AS (
        SELECT
            train_leg_board_alight_time_view.train_leg_id,
            train_leg_board_alight_time_view.board_time,
            board_train_call.train_call_id AS board_train_call_id,
            board_train_call.train_station_id AS board_train_station_id,
            train_leg_board_alight_time_view.alight_time,
            alight_train_call.train_call_id AS alight_train_call_id,
            alight_train_call.train_station_id AS alight_train_station_id,
            train_leg_board_alight_time_view.total_calls,
            (
                train_operator.train_operator_id,
                train_operator.operator_code,
                train_operator.operator_name
            )::transport_user_train_station_operator_out_data AS operator,
            CASE
                WHEN train_brand.train_brand_id IS NOT NULL
                THEN
                (
                    train_brand.train_brand_id,
                    train_brand.brand_code,
                    train_brand.brand_name
                )::transport_user_train_station_operator_out_data
                ELSE NULL
            END AS brand
        FROM (
            SELECT
                train_leg_id,
                MIN(
                    COALESCE(
                        dep_train_call.plan_dep,
                        dep_train_call.plan_arr,
                        dep_train_call.act_dep,
                        dep_train_call.act_arr
                    )
                ) AS board_time,
                MAX(
                    COALESCE(
                        arr_train_call.plan_arr,
                        arr_train_call.act_arr,
                        arr_train_call.plan_dep,
                        arr_train_call.act_dep
                    )
                ) AS alight_time,
                COUNT(train_leg_call.*) AS total_calls
            FROM train_leg_call
            LEFT JOIN train_call arr_train_call
            ON train_leg_call.arr_call_id = arr_train_call.train_call_id
            LEFT JOIN train_call dep_train_call
            ON train_leg_call.dep_call_id = dep_train_call.train_call_id
            GROUP BY train_leg_id
        ) train_leg_board_alight_time_view
        LEFT JOIN train_call board_train_call
        ON train_leg_board_alight_time_view.board_time
            = COALESCE(
                board_train_call.plan_dep,
                board_train_call.act_dep,
                board_train_call.plan_arr,
                board_train_call.act_arr
            )
        LEFT JOIN train_leg_call board_train_leg_call
        ON train_leg_board_alight_time_view.train_leg_id
            = board_train_leg_call.train_leg_id
        AND board_train_call.train_call_id
            = board_train_leg_call.dep_call_id
        LEFT JOIN train_call alight_train_call
        ON train_leg_board_alight_time_view.alight_time
            = COALESCE(
                alight_train_call.plan_arr,
                alight_train_call.act_arr,
                alight_train_call.plan_dep,
                alight_train_call.act_dep
            )
        LEFT JOIN train_leg_call alight_train_leg_call
        ON train_leg_board_alight_time_view.train_leg_id
            = alight_train_leg_call.train_leg_id
        AND alight_train_call.train_call_id
            = alight_train_leg_call.dep_call_id
        INNER JOIN train_service
        ON COALESCE(
            board_train_call.train_service_id,
            alight_train_call.train_service_id
        )
            = train_service.train_service_id
        INNER JOIN train_operator
        ON train_service.train_operator_id = train_operator.train_operator_id
        LEFT JOIN train_brand
        ON train_service.train_brand_id = train_brand.train_brand_id
    ),
    train_station_leg_call_view AS (
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
        ON train_leg_call.dep_call_id = dep_train_call.train_call_id
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
    transport_user_train_station_leg_count_view.calls,
    COALESCE(
        train_station_leg_view.station_legs,
        ARRAY[]::transport_user_train_station_leg_out_data[]
    ) AS station_legs
FROM train_station
INNER JOIN train_operator
ON train_station.train_operator_id = train_operator.train_operator_id
LEFT JOIN train_brand
ON train_station.train_brand_id = train_brand.train_brand_id
INNER JOIN (
    SELECT
        transport_user.user_id,
        train_station.train_station_id,
        COALESCE(train_station_leg_count.boards, 0) AS boards,
        COALESCE(train_station_leg_count.alights, 0) AS alights,
        COALESCE(train_station_leg_count.calls, 0) AS calls
    FROM transport_user
    CROSS JOIN train_station
    LEFT JOIN (
        SELECT
            transport_user_train_leg.user_id,
            train_station_id,
            COUNT(
                CASE WHEN
                    sort_call_time = board_time
                THEN 1
                END
            ) AS boards,
            COUNT(
                CASE WHEN
                    sort_call_time = alight_time
                THEN 1
                END
            ) AS alights,
            COUNT(
                CASE WHEN
                    sort_call_time NOT IN (board_time, alight_time)
                THEN 1
                END
            ) AS calls
        FROM transport_user_train_leg
        INNER JOIN train_station_leg_call_view
        ON transport_user_train_leg.train_leg_id
            = train_station_leg_call_view.train_leg_id
        INNER JOIN train_leg_high_view
        ON train_station_leg_call_view.train_leg_id
            = train_leg_high_view.train_leg_id
        GROUP BY user_id, train_station_id
    ) train_station_leg_count
    ON transport_user.user_id = train_station_leg_count.user_id
    AND train_station.train_station_id = train_station_leg_count.train_station_id
) transport_user_train_station_leg_count_view
ON train_station.train_station_id
    = transport_user_train_station_leg_count_view.train_station_id
LEFT JOIN (
    SELECT
        train_station_leg_call_view.train_station_id,
        transport_user_train_leg.user_id,
        ARRAY_AGG(
            (
                train_station_leg_call_view.train_leg_id,
                (
                    board_train_station.train_station_id,
                    board_train_station.station_crs,
                    board_train_station.station_name
                )::transport_user_train_station_leg_endpoint_out_data,
                (
                    alight_train_station.train_station_id,
                    alight_train_station.station_crs,
                    alight_train_station.station_name
                )::transport_user_train_station_leg_endpoint_out_data,
                train_station_leg_call_view.plan_arr,
                train_station_leg_call_view.act_arr,
                train_station_leg_call_view.plan_dep,
                train_station_leg_call_view.act_dep,
                train_leg_high_view.operator,
                train_leg_high_view.brand,
                train_station_leg_call_before.calls_before,
                train_station_leg_call_before.calls_before,
                train_leg_high_view.total_calls
                    - (train_station_leg_call_before.calls_before + 1)
            )::transport_user_train_station_leg_out_data
            ORDER BY train_station_leg_call_view.sort_call_time DESC
        ) AS station_legs
    FROM train_station_leg_call_view
    LEFT JOIN train_leg_high_view
    ON train_station_leg_call_view.train_leg_id
        = train_leg_high_view.train_leg_id
    INNER JOIN train_station board_train_station
    ON train_leg_high_view.board_train_station_id
        = board_train_station.train_station_id
    INNER JOIN train_station alight_train_station
    ON train_leg_high_view.alight_train_station_id
        = alight_train_station.train_station_id
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
        = train_station_leg_call_before.train_leg_id
    INNER JOIN transport_user_train_leg
    ON train_leg_high_view.train_leg_id = transport_user_train_leg.train_leg_id
    GROUP BY
        train_station_leg_call_view.train_station_id,
        transport_user_train_leg.user_id
) train_station_leg_view
ON train_station.train_station_id = train_station_leg_view.train_station_id
AND transport_user_train_station_leg_count_view.user_id
    = train_station_leg_view.user_id;
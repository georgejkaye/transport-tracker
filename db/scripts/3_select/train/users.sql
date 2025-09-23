DROP FUNCTION select_transport_user_train_leg_by_user_id;
DROP VIEW transport_user_train_leg_view;

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


CREATE FUNCTION select_transport_user_train_leg_by_user_id (
    p_user_id INTEGER,
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
AND (p_search_end IS NULL OR start_datetime <= p_search_end)
ORDER BY start_datetime ASC;
$$;

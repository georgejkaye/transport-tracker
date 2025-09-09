DROP VIEW train_leg_view;

DROP FUNCTION select_train_leg_by_id;

CREATE OR REPLACE VIEW train_leg_view AS
SELECT
    train_leg.train_leg_id,
    train_leg_service.services,
    train_leg_call.calls
FROM train_leg
INNER JOIN (
    SELECT
        train_leg.train_leg_id,
        ARRAY_AGG((
            train_service.train_service_id,
            train_service.unique_identifier,
            train_service.run_date,
            train_service.headcode,
            train_service_call.first_call_time,
            train_service_origin.origins,
            train_service_destination.destinations,
            (
                train_operator.train_operator_id,
                train_operator.operator_code,
                train_operator.operator_name,
                train_operator.bg_colour,
                train_operator.fg_colour
            )::train_leg_operator_out_data,
            CASE WHEN train_brand.train_brand_id IS NULL
            THEN
                NULL
            ELSE
                (
                    train_brand.train_brand_id,
                    train_brand.brand_code,
                    train_brand.brand_name,
                    train_brand.bg_colour,
                    train_brand.fg_colour
                )::train_leg_operator_out_data
            END
        )::train_leg_service_out_data) AS services
    FROM train_leg
    INNER JOIN (
        SELECT DISTINCT
            train_leg.train_leg_id,
            train_service.train_service_id
        FROM train_leg
        INNER JOIN train_leg_call
        ON train_leg.train_leg_id = train_leg_call.train_leg_id
        INNER JOIN train_call
        ON train_leg_call.arr_call_id = train_call.train_call_id
        OR train_leg_call.dep_call_id = train_call.train_call_id
        INNER JOIN train_service
        ON train_call.train_service_id = train_service.train_service_id
    ) train_leg_service_id
    ON train_leg.train_leg_id = train_leg_service_id.train_leg_id
    INNER JOIN train_service
    ON train_leg_service_id.train_service_id = train_service.train_service_id
    INNER JOIN (
        SELECT
            train_call.train_service_id,
            MIN(
                COALESCE(
                    train_call.plan_dep,
                    train_call.act_dep,
                    train_call.plan_arr,
                    train_call.act_arr
                )
            ) AS first_call_time
        FROM train_call
        GROUP BY train_call.train_service_id
    ) train_service_call
    ON train_service.train_service_id = train_service_call.train_service_id
    INNER JOIN (
        SELECT
            train_service_endpoint.train_service_id,
            ARRAY_AGG((
                train_station.train_station_id,
                train_station.station_crs,
                train_station.station_name
            )::train_leg_station_out_data) AS origins
        FROM train_service_endpoint
        INNER JOIN train_station
        ON train_service_endpoint.train_station_id
            = train_station.train_station_id
        WHERE train_service_endpoint.origin = 't'
        GROUP BY train_service_endpoint.train_service_id
    ) train_service_origin
    ON train_service.train_service_id = train_service_origin.train_service_id
    INNER JOIN (
        SELECT
            train_service_endpoint.train_service_id,
            ARRAY_AGG((
                train_station.train_station_id,
                train_station.station_crs,
                train_station.station_name
            )::train_leg_station_out_data) AS destinations
        FROM train_service_endpoint
        INNER JOIN train_station
        ON train_service_endpoint.train_station_id
            = train_station.train_station_id
        WHERE train_service_endpoint.origin = 'f'
        GROUP BY train_service_endpoint.train_service_id
    ) train_service_destination
    ON train_service.train_service_id
        = train_service_destination.train_service_id
    INNER JOIN train_operator
    ON train_service.train_operator_id = train_operator.train_operator_id
    LEFT JOIN train_brand
    ON train_service.train_brand_id = train_brand.train_brand_id
    GROUP BY train_leg.train_leg_id
) train_leg_service
ON train_leg.train_leg_id = train_leg_service.train_leg_id
INNER JOIN (
    SELECT
        train_leg_call.train_leg_id,
        ARRAY_AGG((
            (
                COALESCE(
                    train_station_arr.train_station_id,
                    train_station_dep.train_station_id
                ),
                COALESCE(
                    train_station_arr.station_crs,
                    train_station_dep.station_crs
                ),
                COALESCE(
                    train_station_arr.station_name,
                    train_station_dep.station_name
                )
            )::train_leg_station_out_data,
            COALESCE(
                train_call_arr.platform,
                train_call_dep.platform
            ),
            train_call_arr.plan_arr,
            train_call_arr.act_arr,
            train_call_dep.plan_dep,
            train_call_dep.act_dep,
            train_associated_service_type.type_name,
            train_leg_call.mileage
        )::train_leg_call_out_data
        ORDER BY COALESCE(
            train_call_arr.plan_arr,
            train_call_dep.plan_dep,
            train_call_arr.act_arr,
            train_call_dep.act_dep
        )) AS calls
    FROM train_leg_call
    LEFT JOIN train_call train_call_arr
    ON train_leg_call.arr_call_id = train_call_arr.train_call_id
    LEFT JOIN train_call train_call_dep
    ON train_leg_call.dep_call_id = train_call_dep.train_call_id
    LEFT JOIN train_station train_station_arr
    ON train_call_arr.train_station_id = train_station_arr.train_station_id
    LEFT JOIN train_station train_station_dep
    ON train_call_dep.train_station_id = train_station_dep.train_station_id
    LEFT JOIN train_associated_service_type
    ON train_leg_call.train_associated_type_id
        = train_associated_service_type.train_associated_service_type_id
    GROUP BY train_leg_id
) train_leg_call
ON train_leg.train_leg_id = train_leg_call.train_leg_id;

CREATE OR REPLACE FUNCTION select_train_leg_by_id (
    p_train_leg_id INTEGER
)
RETURNS train_leg_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_view.train_leg_id,
    train_leg_view.services,
    train_leg_view.calls
FROM train_leg_view
WHERE train_leg_view.train_leg_id = p_train_leg_id;
$$;
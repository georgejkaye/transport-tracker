DROP VIEW train_leg_view;

CREATE OR REPLACE VIEW train_leg_view AS
SELECT
    train_leg.train_leg_id,
    train_leg_service.services
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
    INNER JOIN train_brand
    ON train_service.train_brand_id = train_brand.train_brand_id
    GROUP BY train_leg.train_leg_id
) train_leg_service
ON train_leg.train_leg_id = train_leg_service.train_leg_id;
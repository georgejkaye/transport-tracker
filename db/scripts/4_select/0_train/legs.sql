DROP VIEW train_leg_view;

DROP FUNCTION select_train_leg_by_id;

CREATE OR REPLACE VIEW train_leg_view AS
SELECT
    train_leg.train_leg_id,
    train_leg_service.services,
    train_leg_call.calls,
    train_leg_stock.stock
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
ON train_leg.train_leg_id = train_leg_call.train_leg_id
INNER JOIN (
    SELECT
        train_leg_stock_segment_view.train_leg_id,
        ARRAY_AGG((
            (
                train_leg_stock_segment_station_start.train_station_id,
                train_leg_stock_segment_station_start.station_crs,
                train_leg_stock_segment_station_start.station_name
            )::train_leg_station_out_data,
            (
                train_leg_stock_segment_station_end.train_station_id,
                train_leg_stock_segment_station_end.station_crs,
                train_leg_stock_segment_station_end.station_name
            )::train_leg_station_out_data,
            train_leg_stock_report.stock_reports
        )::train_leg_stock_segment_out_data
        ORDER BY train_leg_stock_segment_view.stock_segment_start) AS stock
    FROM (
        SELECT DISTINCT
            train_leg.train_leg_id,
            train_stock_segment_boundary.train_stock_segment_id,
            train_stock_segment_boundary.stock_segment_start,
            CASE
                WHEN train_stock_segment_boundary.stock_segment_start
                     < train_leg_boundary.leg_start
                THEN train_leg_boundary.start_station_id
                ELSE train_stock_segment_boundary.start_station_id
            END AS start_station_id,
            CASE
                WHEN train_stock_segment_boundary.stock_segment_end
                    > train_leg_boundary.leg_end
                THEN train_leg_boundary.end_station_id
                ELSE train_stock_segment_boundary.end_station_id
            END AS end_station_id
        -- train stock segment boundaries
        FROM (
            SELECT
                train_stock_segment.train_stock_segment_id,
                start_call.train_service_id,
                COALESCE(
                    start_call.plan_dep,
                    start_call.act_dep,
                    start_call.plan_arr,
                    start_call.act_arr
                ) AS stock_segment_start,
                start_call.train_station_id AS start_station_id,
                COALESCE(
                    end_call.plan_arr,
                    end_call.act_arr,
                    end_call.plan_dep,
                    end_call.act_dep
                ) AS stock_segment_end,
                end_call.train_station_id AS end_station_id
            FROM train_stock_segment
            INNER JOIN train_call start_call
            ON train_stock_segment.start_call = start_call.train_call_id
            INNER JOIN train_call end_call
            ON train_stock_segment.end_call = end_call.train_call_id
        ) train_stock_segment_boundary
        -- all train calls
        INNER JOIN train_call
        ON train_stock_segment_boundary.train_service_id
            = train_call.train_service_id
        AND
            COALESCE(
                train_call.plan_dep,
                train_call.plan_arr,
                train_call.act_dep,
                train_call.act_arr)
            >= train_stock_segment_boundary.stock_segment_start
        AND
            COALESCE(
                train_call.plan_dep,
                train_call.plan_arr,
                train_call.act_dep,
                train_call.act_arr)
            <= train_stock_segment_boundary.stock_segment_end
        -- all train leg calls
        INNER JOIN train_leg_call
        ON train_leg_call.arr_call_id = train_call.train_call_id
        OR train_leg_call.dep_call_id = train_call.train_call_id
        -- all train legs
        INNER JOIN train_leg
        ON train_leg_call.train_leg_id = train_leg.train_leg_id
        -- table of leg boundary stations
        -- we are going to improve this when we change how leg calls are
        -- specified (#104)
        INNER JOIN (
            WITH train_leg_call_view AS (
                SELECT
                    train_leg_call.train_leg_id,
                    COALESCE(
                        arr_station.train_station_id,
                        dep_station.train_station_id
                    ) AS train_station_id,
                    COALESCE(
                        arr_station.station_crs,
                        dep_station.station_crs
                    ) AS station_crs,
                    COALESCE(
                        arr_station.station_name,
                        dep_station.station_name
                    ) AS station_name,
                    arr_call.plan_arr,
                    arr_call.act_arr,
                    dep_call.plan_dep,
                    dep_call.act_dep
                FROM train_leg_call
                LEFT JOIN train_call arr_call
                ON train_leg_call.arr_call_id = arr_call.train_call_id
                LEFT JOIN train_station arr_station
                ON arr_call.train_station_id = arr_station.train_station_id
                LEFT JOIN train_call dep_call
                ON train_leg_call.dep_call_id = dep_call.train_call_id
                LEFT JOIN train_station dep_station
                ON dep_call.train_station_id = dep_station.train_station_id
            )
            SELECT
                train_leg_time.train_leg_id,
                train_leg_start.train_station_id AS start_station_id,
                train_leg_time.leg_start AS leg_start,
                train_leg_end.train_station_id AS end_station_id,
                train_leg_time.leg_end AS leg_end
            FROM (
                SELECT
                    train_leg_call_view.train_leg_id,
                    MIN(
                        COALESCE(
                            train_leg_call_view.plan_dep,
                            train_leg_call_view.act_dep,
                            train_leg_call_view.plan_arr,
                            train_leg_call_view.act_arr
                        )
                    ) AS leg_start,
                    MAX(
                        COALESCE(
                            train_leg_call_view.plan_arr,
                            train_leg_call_view.act_arr,
                            train_leg_call_view.plan_dep,
                            train_leg_call_view.act_dep
                        )
                    ) AS leg_end
                FROM train_leg_call_view
                GROUP BY train_leg_call_view.train_leg_id
            ) train_leg_time
            INNER JOIN train_leg_call_view train_leg_start
            ON train_leg_time.train_leg_id = train_leg_start.train_leg_id
            AND train_leg_time.leg_start
                = COALESCE(
                    train_leg_start.plan_dep,
                    train_leg_start.plan_arr,
                    train_leg_start.act_dep,
                    train_leg_start.act_arr
                )
            INNER JOIN train_leg_call_view train_leg_end
            ON train_leg_time.train_leg_id = train_leg_end.train_leg_id
            AND train_leg_time.leg_end
                = COALESCE(
                    train_leg_end.plan_arr,
                    train_leg_end.plan_dep,
                    train_leg_end.act_arr,
                    train_leg_end.act_dep
                )
        ) train_leg_boundary
        ON train_leg.train_leg_id = train_leg_boundary.train_leg_id
    ) train_leg_stock_segment_view
    INNER JOIN train_station train_leg_stock_segment_station_start
    ON train_leg_stock_segment_view.start_station_id
        = train_leg_stock_segment_station_start.train_station_id
    INNER JOIN train_station train_leg_stock_segment_station_end
    ON train_leg_stock_segment_view.end_station_id
        = train_leg_stock_segment_station_end.train_station_id
    -- table of stock reports
    INNER JOIN (
        SELECT
            train_stock_segment_report.train_stock_segment_id,
            ARRAY_AGG((
                train_stock_report.stock_class,
                train_stock_report.stock_subclass,
                train_stock_report.stock_number,
                train_stock_report.stock_cars
            )::train_leg_stock_report_out_data) AS stock_reports
        FROM train_stock_segment_report
        INNER JOIN train_stock_report
        ON train_stock_segment_report.train_stock_report_id
            = train_stock_report.train_stock_report_id
        GROUP BY train_stock_segment_report.train_stock_segment_id
    ) train_leg_stock_report
    ON train_leg_stock_segment_view.train_stock_segment_id
        = train_leg_stock_report.train_stock_segment_id
    GROUP BY train_leg_stock_segment_view.train_leg_id
) train_leg_stock
ON train_leg.train_leg_id = train_leg_stock.train_leg_id;

CREATE OR REPLACE FUNCTION select_train_leg_by_id (
    p_train_leg_id INTEGER
)
RETURNS SETOF train_leg_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_view.train_leg_id,
    train_leg_view.services,
    train_leg_view.calls,
    train_leg_view.stock
FROM train_leg_view
WHERE train_leg_view.train_leg_id = p_train_leg_id;
$$;
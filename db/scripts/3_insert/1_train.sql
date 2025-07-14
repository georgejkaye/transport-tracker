CREATE OR REPLACE FUNCTION insert_leg(
    p_user_id INTEGER[],
    p_leg train_leg_in_data
)
RETURNS VOID
LANGUAGE plpgsql
AS
$$
DECLARE
    v_train_leg_id INT;
    v_train_call_with_service_id
BEGIN
    INSERT INTO train_leg (distance)
    VALUES (p_leg.leg_distance)
    RETURNING train_leg_id INTO v_train_leg_id;

    INSERT INTO train_service (
        unique_identifier,
        run_date,
        headcode,
        operator_id,
        brand_id,
        power
    )
    SELECT
        v_service.unique_identifier,
        v_service.run_data,
        v_service.headcode,
        v_service.operator_id,
        v_service.brand_id,
        v_service.power
    FROM UNNEST(p_leg.leg_services) AS v_service;

    INSERT INTO train_service_endpoint (
        train_service_id,
        train_station_id,
        origin
    ) SELECT
        (
            SELECT train_service_id
            FROM train_service
            WHERE train_service.unique_identifier = v_endpoint.unique_identifier
            AND train_service.run_date = v_endpoint.run_date
        ),
        (
            SELECT train_station_id
            FROM train_station
            INNER JOIN train_station_name
            ON train_station.train_station_id
                = train_station_name.train_station_id
            WHERE train_station.station_name = v_endpoint.station_name
            OR train_station_name.alternate_station_name
                = v_endpoint.station_name
        )
        v_endpoint.origin
    FROM SELECT UNNEST(p_leg.service_endpoints) AS v_endpoint;

    INSERT INTO train_call (
        train_service_id,
        train_station_id,
        platform,
        plan_arr,
        plan_dep,
        act_arr,
        act_dep,
        mileage
    ) SELECT
        (
            SELECT train_service_id
            FROM train_service
            WHERE train_service.unique_identifier = v_call.unique_identifier
            AND train_service.run_date = v_call.run_date
        ),
        (
            SELECT train_station_id
            FROM train_station
            INNER JOIN train_station_name
            ON train_station.train_station_id
                = train_station_name.train_station_id
            WHERE train_station.station_name = v_call.station_name
            OR train_station_name.alternate_station_name
                = v_call.station_name
        ),
        v_call.platform,
        v_call.plan_arr,
        v_call.plan_dep,
        v_call.act_arr,
        v_call.act_dep,
        v_call.mileage
    FROM UNNEST(p_leg.service_calls) AS p_call;

    INSERT INTO train_associated_service (
        call_id,
        associated_type_id,
        associated_service_id
    ) SELECT
        (
            SELECT call_id
            FROM train_call
            INNER JOIN train_service
            ON train_call.train_service_id = train_service.train_service_id
            WHERE train_service.unique_identifier = v_assoc.unique_identifier
            AND train_service.run_date = v_assoc.run_date
            AND train_call.plan_arr = v_assoc.plan_arr
            AND train_call.plan_dep = v_assoc.plan_dep
            AND train_call.act_arr = v_assoc.plan_arr
            AND train_call.act_dep = v_assoc.act_dep
        ),
        (
            SELECT train_service_id
            FROM train_service
            WHERE train_service.unique_identifier
                = v_assoc.assoc_unique_identifier
            AND train_service.run_date = v_assoc.assoc_run_date
        ),
        v_assoc.assoc_type
    FROM UNNEST(p_leg.service_associations) AS v_assoc;

    INSERT INTO train_leg_call(
        train_leg_id,
        arr_call_id,
        dep_call_id,
        mileage,
        associated_type_id
    )
    SELECT
        v_train_leg_id,
        (
            SELECT call_id
            FROM train_call
            INNER JOIN train_station
            ON train_call.station_id = train_station.station_id
            INNER JOIN train_service
            ON train_call.service_id = train_service.service_id
            WHERE train_station.station_crs = v_legcall.station_crs
            AND train_service.unique_identifier = v_legcall.start_call_service_uid
            AND train_service.run_date = v_legcall.start_call_service_run_date
            AND train_call.plan_arr = v_legcall.start_call_plan_arr
            AND train_call.act_arr = v_legcall.start_call_act_arr
            AND train_call.plan_dep = v_legcall.start_call_plan_dep
            AND train_call.act_dep = v_legcall.start_call_act_dep
        ),
        (
            SELECT call_id
            FROM train_call
            INNER JOIN train_station
            ON train_call.station_id = train_station.station_id
            INNER JOIN train_service
            ON train_call.service_id = train_service.service_id
            WHERE train_station.station_crs = v_legcall.station_crs
            AND train_service.unique_identifier = v_legcall.dep_call_service_uid
            AND train_service.run_date = v_legcall.dep_call_service_run_date
            AND train_call.plan_arr = v_legcall.dep_call_plan_arr
            AND train_call.act_arr = v_legcall.dep_call_act_arr
            AND train_call.plan_dep = v_legcall.dep_call_plan_dep
            AND train_call.act_dep = v_legcall.dep_call_act_dep
        ),
        v_legcall.mileage,
        v_legcall.associated_type_id
    FROM UNNEST(p_leg.leg_calls) AS v_legcall;

    INSERT INTO train_stock_segment(start_call, end_call)
        SELECT
        (
            SELECT call_id
            FROM train_call
            INNER JOIN train_station
            ON train_call.station_id = train_station.station_id
            INNER JOIN train_service
            ON train_call.service_id = train_service.service_id
            WHERE train_station.station_crs = v_stock_segment.station_crs
            AND train_service.unique_identifier = v_stock_segment.arr_call_service_uid
            AND train_service.run_date = v_stock_segment.arr_call_service_run_date
            AND train_call.plan_arr = v_stock_segment.arr_call_plan_arr
            AND train_call.act_arr = v_stock_segment.arr_call_act_arr
            AND train_call.plan_dep = v_stock_segment.arr_call_plan_dep
            AND train_call.act_dep = v_stock_segment.arr_call_act_dep
        ),
        (
            SELECT call_id
            FROM train_call
            INNER JOIN train_station
            ON train_call.station_id = train_station.station_id
            INNER JOIN train_service
            ON train_call.service_id = train_service.service_id
            WHERE train_station.station_crs = v_stock_segment.station_crs
            AND train_service.unique_identifier = v_stock_segment.end_call_service_uid
            AND train_service.run_date = v_stock_segment.end_call_service_run_date
            AND train_call.plan_arr = v_stock_segment.end_call_plan_arr
            AND train_call.act_arr = v_stock_segment.end_call_act_arr
            AND train_call.plan_dep = v_stock_segment.end_call_plan_dep
            AND train_call.act_dep = v_stock_segment.end_call_act_dep
        ),
        FROM UNNEST(p_leg.leg_stock) AS v_stockreport
        ON CONFLICT DO NOTHING;

    INSERT INTO train_stock_report (
        stock_class,
        stock_subclass,
        stock_number,
        stock_cars
    ) SELECT
        v_stockreport.stock_class,
        v_stockreport.stock_subclass,
        v_stockreport.stock_number,
        v_stockreport.stock_cars
    FROM UNNEST(p_leg.leg_stock) AS v_stockreport
    ON CONFLICT DO NOTHING;

    INSERT INTO TrainStockSegmentReport(
        stock_segment_id,
        stock_report_id
    ) SELECT
        (
            SELECT stock_segment_id
            FROM train_stock_segment
            WHERE start_call = (
                SELECT call_id
                FROM train_call
                INNER JOIN train_station
                ON train_call.station_id = train_station.station_id
                INNER JOIN train_service
                ON train_call.service_id
                    = train_service.service_id
                WHERE train_station.station_crs
                    = v_stock_segment.station_crs
                AND train_service.unique_identifier
                    = v_stock_segment.arr_call_service_uid
                AND train_service.run_date
                    = v_stock_segment.arr_call_service_run_date
                AND train_call.plan_arr
                    = v_stock_segment.arr_call_plan_arr
                AND train_call.act_arr
                    = v_stock_segment.arr_call_act_arr
                AND train_call.plan_dep
                    = v_stock_segment.arr_call_plan_dep
                AND train_call.act_dep
                    = v_stock_segment.arr_call_act_dep
            )
            AND end_call = (
                SELECT call_id
                FROM train_call
                INNER JOIN train_station
                ON train_call.station_id = train_station.station_id
                INNER JOIN train_service
                ON train_call.service_id = train_service.service_id
                WHERE train_station.station_crs
                    = v_stock_segment.station_crs
                AND train_service.unique_identifier
                    = v_stock_segment.end_call_service_uid
                AND train_service.run_date
                    = v_stock_segment.end_call_service_run_date
                AND train_call.plan_arr
                    = v_stock_segment.end_call_plan_arr
                AND train_call.act_arr
                    = v_stock_segment.end_call_act_arr
                AND train_call.plan_dep
                    = v_stock_segment.end_call_plan_dep
                AND train_call.act_dep
                    = v_stock_segment.end_call_act_dep
            ),
        ),
        (
            SELECT stock_report_id
            FROM train_stock_report
            WHERE train_stock_report.stock_class
            IS NOT DISTINCT FROM v_stockreport.stock_class
            AND train_stock_report.stock_subclass
            IS NOT DISTINCT FROM v_stockreport.stock_subclass
            AND train_stock_report.stock_number
            IS NOT DISTINCT FROM v_stockreport.stock_number
            AND train_stock_report.stock_cars
            IS NOT DISTINCT FROM v_stockreport.stock_cars
        )
    FROM UNNEST(p_leg.leg_stock) AS v_stockreport
    ON CONFLICT DO NOTHING;

    INSERT INTO transport_user_train_leg (
        user_id,
        train_sequence_id
    )
    VALUES (v_user, v_train_sequence_id)
    FROM UNNEST(p_users) AS v_user;
END;
$$;
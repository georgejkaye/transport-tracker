DROP FUNCTION insert_leg;

CREATE OR REPLACE FUNCTION insert_leg (
    p_users INTEGER[],
    p_leg train_leg_in_data
)
RETURNS VOID
LANGUAGE plpgsql
AS
$$
DECLARE
    v_train_leg_id INT;
    v_service_ids INT[];
    v_call_ids INT[];
BEGIN
    INSERT INTO train_leg (distance)
    VALUES (p_leg.leg_distance)
    RETURNING train_leg_id INTO v_train_leg_id;

    WITH new_train_service(train_service_id) AS (
    INSERT INTO train_service (
        unique_identifier,
        run_date,
        headcode,
        train_operator_id,
        train_brand_id,
        power
    )
    SELECT
        v_service.unique_identifier,
        v_service.run_date,
        v_service.headcode,
        v_service.operator_id,
        v_service.brand_id,
        v_service.power
    FROM UNNEST(p_leg.leg_services) AS v_service
    ON CONFLICT DO NOTHING
    RETURNING train_service_id)
    SELECT array_agg(train_service_id)
    FROM new_train_service
    INTO v_service_ids;

    RAISE LOG 'Inserted train_service_id: %', v_service_ids;

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
            SELECT train_station.train_station_id
            FROM train_station
            LEFT JOIN train_station_name
            ON train_station.train_station_id
                = train_station_name.train_station_id
            WHERE train_station.station_name = v_endpoint.station_name
            OR train_station_name.alternate_station_name
                = v_endpoint.station_name
        ),
        v_endpoint.origin
    FROM UNNEST(p_leg.service_endpoints) AS v_endpoint
    ON CONFLICT DO NOTHING;

    WITH new_train_call(train_call_id) AS (
    INSERT INTO train_call (
        train_service_id,
        train_station_id,
        platform,
        plan_arr,
        act_arr,
        plan_dep,
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
            SELECT train_station.train_station_id
            FROM train_station
            LEFT JOIN train_station_name
            ON train_station.train_station_id
                = train_station_name.train_station_id
            WHERE train_station.station_crs = v_call.station_crs
        ),
        v_call.platform,
        v_call.plan_arr,
        v_call.act_arr,
        v_call.plan_dep,
        v_call.act_dep,
        v_call.mileage
    FROM UNNEST(p_leg.service_calls) AS v_call
    ON CONFLICT DO NOTHING
    RETURNING train_call_id)
    SELECT array_agg(train_call_id)
    FROM new_train_call
    INTO v_call_ids;

    RAISE LOG 'Inserted train_call_ids: %', v_call_ids;

    INSERT INTO train_associated_service (
        call_id,
        associated_type_id,
        associated_service_id
    ) SELECT
        (
            SELECT train_call_id
            FROM train_call
            INNER JOIN train_service
            ON train_call.train_service_id = train_service.train_service_id
            WHERE train_service.unique_identifier = v_assoc.unique_identifier
            AND train_service.run_date = v_assoc.run_date
            AND (
                v_assoc.plan_arr IS NULL
                OR train_call.plan_arr = v_assoc.plan_arr)
            AND (
                v_assoc.act_arr IS NULL
                OR train_call.act_arr = v_assoc.act_arr)
            AND (
                v_assoc.plan_dep IS NULL
                OR train_call.plan_dep = v_assoc.plan_dep)
            AND (
                v_assoc.act_dep IS NULL
                OR train_call.act_dep = v_assoc.act_dep)
        ),
        v_assoc.assoc_type,
        (
            SELECT train_service_id
            FROM train_service
            WHERE train_service.unique_identifier
                = v_assoc.assoc_unique_identifier
            AND train_service.run_date = v_assoc.assoc_run_date
        )
    FROM UNNEST(p_leg.service_associations) AS v_assoc
    ON CONFLICT DO NOTHING;

    INSERT INTO train_leg_call (
        train_leg_id,
        arr_call_id,
        dep_call_id,
        mileage,
        associated_type_id
    )
    SELECT
        v_train_leg_id,
        (
            SELECT train_call_id
            FROM train_call
            INNER JOIN train_station
            ON train_call.train_station_id = train_station.train_station_id
            INNER JOIN train_service
            ON train_call.train_service_id = train_service.train_service_id
            WHERE train_station.station_crs
                = v_leg_call.station_crs
            AND train_service.unique_identifier
                = v_leg_call.arr_call_service_uid
            AND train_service.run_date
                = v_leg_call.arr_call_service_run_date
            AND (
                v_leg_call.arr_call_plan_arr IS NULL
                OR train_call.plan_arr = v_leg_call.arr_call_plan_arr)
            AND (
                v_leg_call.arr_call_act_arr IS NULL
                OR train_call.act_arr = v_leg_call.arr_call_act_arr)
            AND (
                v_leg_call.arr_call_plan_dep IS NULL
                OR train_call.plan_dep = v_leg_call.arr_call_plan_dep)
            AND (
                v_leg_call.arr_call_act_dep IS NULL
                OR train_call.act_dep = v_leg_call.arr_call_act_dep)
        ),
        (
            SELECT train_call_id
            FROM train_call
            INNER JOIN train_station
            ON train_call.train_station_id = train_station.train_station_id
            INNER JOIN train_service
            ON train_call.train_service_id = train_service.train_service_id
            WHERE train_station.station_crs = v_leg_call.station_crs
            AND train_service.unique_identifier
                = v_leg_call.dep_call_service_uid
            AND train_service.run_date
                = v_leg_call.dep_call_service_run_date
            AND (
                v_leg_call.dep_call_plan_arr IS NULL
                OR train_call.plan_arr = v_leg_call.dep_call_plan_arr)
            AND (
                v_leg_call.dep_call_act_arr IS NULL
                OR train_call.act_arr = v_leg_call.dep_call_act_arr)
            AND (
                v_leg_call.dep_call_plan_dep IS NULL
                OR train_call.plan_dep = v_leg_call.dep_call_plan_dep)
            AND (
                v_leg_call.dep_call_act_dep IS NULL
                OR train_call.act_dep = v_leg_call.dep_call_act_dep)
        ),
        v_leg_call.mileage,
        v_leg_call.associated_type_id
    FROM UNNEST(p_leg.leg_calls) AS v_leg_call
    ON CONFLICT DO NOTHING;

    INSERT INTO train_stock_segment(start_call, end_call)
        SELECT
        (
            SELECT train_call_id
            FROM train_call
            INNER JOIN train_station
            ON train_call.train_station_id = train_station.train_station_id
            INNER JOIN train_service
            ON train_call.train_service_id = train_service.train_service_id
            WHERE train_station.station_crs
                = v_stock_report.start_call_station_crs
            AND train_service.unique_identifier
                = v_stock_report.start_call_service_uid
            AND train_service.run_date
                = v_stock_report.start_call_service_run_date
            AND (
                v_stock_report.start_call_plan_dep IS NULL
                OR train_call.plan_dep = v_stock_report.start_call_plan_dep)
            AND (
                v_stock_report.start_call_act_dep IS NULL
                OR train_call.act_dep = v_stock_report.start_call_act_dep)
        ),
        (
            SELECT train_call_id
            FROM train_call
            INNER JOIN train_station
            ON train_call.train_station_id = train_station.train_station_id
            INNER JOIN train_service
            ON train_call.train_service_id = train_service.train_service_id
            WHERE train_station.station_crs
                = v_stock_report.end_call_station_crs
            AND train_service.unique_identifier
                = v_stock_report.end_call_service_uid
            AND train_service.run_date
                = v_stock_report.end_call_service_run_date
            AND (
                v_stock_report.end_call_plan_arr IS NULL
                OR train_call.plan_arr = v_stock_report.end_call_plan_arr)
            AND (
                v_stock_report.end_call_act_arr IS NULL
                OR train_call.act_arr = v_stock_report.end_call_act_arr)
        )
        FROM UNNEST(p_leg.leg_stock) AS v_stock_report
        ON CONFLICT DO NOTHING;

    INSERT INTO train_stock_report (
        stock_class,
        stock_subclass,
        stock_number,
        stock_cars
    ) SELECT
        v_stock_report.stock_class,
        v_stock_report.stock_subclass,
        v_stock_report.stock_number,
        v_stock_report.stock_cars
    FROM UNNEST(p_leg.leg_stock) AS v_stock_report
    ON CONFLICT DO NOTHING;

    INSERT INTO train_stock_segment_report(
        train_stock_segment_id,
        train_stock_report_id
    ) SELECT
        (
            SELECT train_stock_segment_id
            FROM train_stock_segment
            WHERE start_call = (
                SELECT train_call_id
                FROM train_call
                INNER JOIN train_station
                ON train_call.train_station_id = train_station.train_station_id
                INNER JOIN train_service
                ON train_call.train_service_id
                    = train_service.train_service_id
                WHERE train_station.station_crs
                    = v_stock_report.start_call_station_crs
                AND train_service.unique_identifier
                    = v_stock_report.start_call_service_uid
                AND train_service.run_date
                    = v_stock_report.start_call_service_run_date
                AND (
                    v_stock_report.start_call_plan_dep IS NULL
                    OR train_call.plan_dep = v_stock_report.start_call_plan_dep)
                AND (
                    v_stock_report.start_call_act_dep IS NULL
                    OR train_call.act_dep = v_stock_report.start_call_act_dep)
            )
            AND end_call = (
                SELECT train_call_id
                FROM train_call
                INNER JOIN train_station
                ON train_call.train_station_id = train_station.train_station_id
                INNER JOIN train_service
                ON train_call.train_service_id = train_service.train_service_id
                WHERE train_station.station_crs
                    = v_stock_report.end_call_station_crs
                AND train_service.unique_identifier
                    = v_stock_report.end_call_service_uid
                AND train_service.run_date
                    = v_stock_report.end_call_service_run_date
                AND (
                    v_stock_report.end_call_plan_arr IS NULL
                    OR train_call.plan_arr = v_stock_report.end_call_plan_arr)
                AND (
                    v_stock_report.end_call_act_arr IS NULL
                    OR train_call.act_arr = v_stock_report.end_call_act_arr)
            )
        ),
        (
            SELECT train_stock_report_id
            FROM train_stock_report
            WHERE train_stock_report.stock_class
            IS NOT DISTINCT FROM v_stock_report.stock_class
            AND train_stock_report.stock_subclass
            IS NOT DISTINCT FROM v_stock_report.stock_subclass
            AND train_stock_report.stock_number
            IS NOT DISTINCT FROM v_stock_report.stock_number
            AND train_stock_report.stock_cars
            IS NOT DISTINCT FROM v_stock_report.stock_cars
            ORDER BY train_stock_report_id
            LIMIT 1
        )
    FROM UNNEST(p_leg.leg_stock) AS v_stock_report
    ON CONFLICT DO NOTHING;

    INSERT INTO transport_user_train_leg (
        user_id,
        train_leg_id
    )
    SELECT v_user, v_train_leg_id
    FROM UNNEST(p_users) AS v_user;
END;
$$;
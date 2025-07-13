CREATE OR REPLACE FUNCTION InsertServices(
    p_services TrainServiceInData[],
    p_endpoints TrainServiceEndpointInData[],
    p_calls TrainCallInData[],
    p_assocs TrainAssociatedServiceInData[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
DECLARE
    v_operator_id INT;
    v_brand_id INT;
BEGIN
    INSERT INTO TrainService(
        service_id,
        run_date,
        headcode,
        operator_id,
        brand_id,
        power
    ) SELECT
        v_service.service_id,
        v_service.run_date,
        v_service.headcode,
        (SELECT GetOperatorId(v_service.operator_code, v_service.run_date)),
        (SELECT GetBrandId(v_service.brand_code, v_service.run_date)),
        v_service.power
    FROM UNNEST(p_services) AS v_service
    ON CONFLICT DO NOTHING;
    INSERT INTO TrainServiceEndpoint(
        service_id,
        run_date,
        station_crs,
        origin
    ) SELECT
        v_endpoint.service_id,
        v_endpoint.run_date,
        v_endpoint.station_crs,
        v_endpoint.origin
    FROM UNNEST(p_endpoints) AS v_endpoint
    ON CONFLICT DO NOTHING;
    INSERT INTO TrainCall(
        service_id,
        run_date,
        station_crs,
        platform,
        plan_arr,
        plan_dep,
        act_arr,
        act_dep,
        mileage
    ) SELECT
        v_call.service_id,
        v_call.run_date,
        v_call.station_crs,
        v_call.platform,
        v_call.plan_arr,
        v_call.plan_dep,
        v_call.act_arr,
        v_call.act_dep,
        v_call.mileage
    FROM UNNEST(p_calls) AS v_call
    ON CONFLICT DO NOTHING;
    INSERT INTO TrainAssociatedService(
        call_id,
        associated_id,
        associated_run_date,
        associated_type
    ) SELECT
        (SELECT GetCallFromLegCall(
            v_assoc.service_id,
            v_assoc.run_date,
            v_assoc.station_crs,
            v_assoc.plan_arr,
            v_assoc.plan_dep,
            v_assoc.act_arr,
            v_assoc.act_dep
        )),
        v_assoc.assoc_id,
        v_assoc.assoc_run_date,
        v_assoc.assoc_type
    FROM UNNEST(p_assocs) AS v_assoc
    ON CONFLICT DO NOTHING;
END;
$$;

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

    INSERT INTO train_leg_call(
        train_sequence_id,
        arr_call_id,
        dep_call_id,
        mileage,
        assoc_type
    )
    SELECT
        v_sequence_id,
        (SELECT GetCallFromLegCall(
            v_legcall.arr_call_service_id,
            v_legcall.arr_call_run_date,
            v_legcall.arr_call_station_crs,
            v_legcall.arr_call_plan_arr,
            v_legcall.arr_call_plan_dep,
            v_legcall.arr_call_act_arr,
            v_legcall.arr_call_act_dep
        )),
        (SELECT GetCallFromLegCall(
            v_legcall.dep_call_service_id,
            v_legcall.dep_call_run_date,
            v_legcall.dep_call_station_crs,
            v_legcall.dep_call_plan_arr,
            v_legcall.dep_call_plan_dep,
            v_legcall.dep_call_act_arr,
            v_legcall.dep_call_act_dep
        )),
        v_legcall.mileage,
        v_legcall.assoc_type
    FROM UNNEST(p_legcalls) AS v_legcall;
    INSERT INTO TrainStockSegment(start_call, end_call)
        SELECT
            (SELECT GetCallFromLegCall(
                v_stockreport.arr_call_service_id,
                v_stockreport.arr_call_run_date,
                v_stockreport.arr_call_station_crs,
                v_stockreport.arr_call_plan_arr,
                v_stockreport.arr_call_plan_dep,
                v_stockreport.arr_call_act_arr,
                v_stockreport.arr_call_act_dep
            )),
            (SELECT GetCallFromLegCall(
                v_stockreport.dep_call_service_id,
                v_stockreport.dep_call_run_date,
                v_stockreport.dep_call_station_crs,
                v_stockreport.dep_call_plan_arr,
                v_stockreport.dep_call_plan_dep,
                v_stockreport.dep_call_act_arr,
                v_stockreport.dep_call_act_dep
            ))
        FROM UNNEST(p_stockreports) AS v_stockreport
        ON CONFLICT DO NOTHING;
    INSERT INTO TrainStockReport(
        stock_class,
        stock_subclass,
        stock_number,
        stock_cars
    ) SELECT
        v_stockreport.stock_class,
        v_stockreport.stock_subclass,
        v_stockreport.stock_number,
        v_stockreport.stock_cars
    FROM UNNEST(p_stockreports) AS v_stockreport
    ON CONFLICT DO NOTHING;
    INSERT INTO TrainStockSegmentReport(
        stock_segment_id,
        stock_report_id
    ) SELECT
        (SELECT GetStockSegmentId(
            (SELECT GetCallFromLegCall(
                v_stockreport.arr_call_service_id,
                v_stockreport.arr_call_run_date,
                v_stockreport.arr_call_station_crs,
                v_stockreport.arr_call_plan_arr,
                v_stockreport.arr_call_plan_dep,
                v_stockreport.arr_call_act_arr,
                v_stockreport.arr_call_act_dep
            )),
            (SELECT GetCallFromLegCall(
                v_stockreport.dep_call_service_id,
                v_stockreport.dep_call_run_date,
                v_stockreport.dep_call_station_crs,
                v_stockreport.dep_call_plan_arr,
                v_stockreport.dep_call_plan_dep,
                v_stockreport.dep_call_act_arr,
                v_stockreport.dep_call_act_dep
            ))
        )),
        (SELECT GetStockReportId(
            v_stockreport.stock_class,
            v_stockreport.stock_subclass,
            v_stockreport.stock_number,
            v_stockreport.stock_cars
        ))
    FROM UNNEST(p_stockreports) AS v_stockreport
    ON CONFLICT DO NOTHING;

    INSERT INTO train_leg(user_id, train_sequence_id)
    VALUES (v_user, v_train_sequence_id)
    FROM UNNEST(p_users) AS v_user;
END;
$$;
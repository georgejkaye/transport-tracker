DROP VIEW transport_user_train_leg_view;

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
            train_service_call.first_call_time
        )::train_leg_train_service_out_data) AS services
    FROM train_leg
    INNER JOIN train_leg_call
    ON train_leg.train_leg_id = train_leg_call.train_leg_id
    INNER JOIN train_call
    ON train_leg_call.arr_call_id = train_call.train_call_id
    OR train_leg_call.dep_call_id = train_call.train_call_id
    INNER JOIN train_service
    ON train_call.train_service_id = train_service.train_service_id
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
    GROUP BY train_leg.train_leg_id
) train_leg_service
ON train_leg.train_leg_id = train_leg_service.train_leg_id;


    SELECT *
    FROM train_leg
    INNER JOIN train_leg_call
    ON train_leg.train_leg_id = train_leg_call.train_leg_id
    INNER JOIN train_call
    ON train_leg_call.arr_call_id = train_call.train_call_id
    OR train_leg_call.dep_call_id = train_call.train_call_id
    INNER JOIN train_service
    ON train_call.train_service_id = train_service.train_service_id
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



DROP FUNCTION select_legs_by_id (
    p_leg_ids INTEGER[]
)
CREATE OR REPLACE FUNCTION insert_bus_leg (
    p_users INTEGER_NOTNULL[],
    p_leg bus_leg_in_data_notnull
) RETURNS SETOF insert_bus_leg_result
LANGUAGE plpgsql
AS
$$
DECLARE
    v_bus_journey bus_journey_in_data_notnull;
    v_bus_journey_ids INTEGER_NOTNULL[] := '{}';
    v_bus_journey_id INTEGER_NOTNULL;
    v_bus_leg_id INTEGER_NOTNULL := 0;
BEGIN
    INSERT INTO bus_leg DEFAULT VALUES
    RETURNING bus_leg_id INTO v_bus_leg_id;

    FOREACH v_bus_journey IN ARRAY p_leg.journeys
    LOOP
        SELECT insert_bus_journey(v_bus_journey.journey)
        INTO v_bus_journey_id;
        v_bus_journey_ids := ARRAY_APPEND(
            v_bus_journey_ids,
            v_bus_journey_id
        );

        INSERT INTO bus_leg_journey (
            bus_leg_id,
            bus_journey_id,
            board_call_id,
            alight_call_id
        )
        VALUES (
            v_bus_leg_id,
            v_bus_journey_id,
            (
                SELECT bus_call_id
                FROM bus_call
                WHERE bus_journey_id = v_bus_journey_id
                AND stop_atco = v_bus_journey.start_atco
                AND (
                    plan_dep = v_bus_journey.start_time
                    OR plan_arr = v_bus_journey.start_time
                )
            ),
            (
                SELECT bus_call_id
                FROM bus_call
                WHERE bus_journey_id = v_bus_journey_id
                AND stop_atco = v_bus_journey.end_atco
                AND (
                    plan_dep = v_bus_journey.start_time
                    OR plan_arr = v_bus_journey.start_time
                )
            )
        );
    END LOOP;

    INSERT INTO transport_user_bus_leg (
        user_id,
        bus_leg_id
    ) SELECT
        v_user,
        v_bus_leg_id
    FROM UNNEST(p_users) AS v_user;

    RAISE LOG 'Inserted bus_leg_id: %', v_bus_leg_id;

    RETURN QUERY SELECT v_bus_leg_id;
END;
$$;

CREATE OR REPLACE FUNCTION insert_bus_calls (
    p_journey_id INTEGER_NOTNULL,
    p_calls bus_call_in_data_notnull[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusCall (
        bus_journey_id,
        call_index,
        bus_stop_id,
        plan_arr,
        act_arr,
        plan_dep,
        act_dep
    ) SELECT
        p_journey_id,
        v_call.call_index,
        (SELECT bus_stop_id
        FROM BusStop
        WHERE v_call.stop_atco = BusStop.atco_code),
        v_call.plan_arr,
        v_call.act_arr,
        v_call.plan_dep,
        v_call.act_dep
    FROM UNNEST(p_calls) AS v_call;
END;
$$;

CREATE OR REPLACE FUNCTION insert_bus_journey (
    p_journey bus_journey_in_data_notnull
) RETURNS INT
LANGUAGE plpgsql
AS
$$
DECLARE
    v_bus_journey_id INT;
BEGIN
    INSERT INTO BusJourney (
        bus_service_id,
        bus_vehicle_id
    ) VALUES (p_journey.service_id, p_journey.vehicle_id)
    RETURNING bus_journey_id INTO v_bus_journey_id;
    PERFORM insert_bus_calls(v_bus_journey_id, p_journey.journey_calls);
    RETURN v_bus_journey_id;
END;
$$;
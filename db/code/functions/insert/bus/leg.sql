CREATE OR REPLACE FUNCTION insert_bus_leg (
    p_users INTEGER_NOTNULL[],
    p_leg bus_leg_in_data_notnull
) RETURNS SETOF insert_bus_leg_result
LANGUAGE plpgsql
AS
$$
DECLARE
    v_bus_journey_id INTEGER_NOTNULL := 0;
    v_bus_leg_id INTEGER_NOTNULL := 0;
BEGIN
    SELECT insert_bus_journey(p_leg.journey) INTO v_bus_journey_id;
    INSERT INTO BusLeg (
        user_id,
        bus_journey_id,
        board_call_index,
        alight_call_index
    ) SELECT
        v_user,
        v_bus_journey_id,
        p_leg.board_index,
        p_leg.alight_index
    FROM UNNEST(p_users) AS v_user
    RETURNING bus_leg_id INTO v_bus_leg_id;

    RETURN QUERY SELECT v_bus_leg_id;
END;
$$;

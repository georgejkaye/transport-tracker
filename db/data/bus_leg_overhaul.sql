CREATE TABLE IF NOT EXISTS bus_leg_journey (
    bus_leg_journey_id SERIAL PRIMARY KEY,
    bus_leg_id INTEGER NOT NULL,
    bus_journey_id INTEGER NOT NULL,
    start_call_id INTEGER NOT NULL,
    end_call_id INTEGER NOT NULL,
    FOREIGN KEY(bus_leg_id) REFERENCES bus_leg(bus_leg_id),
    FOREIGN KEY(bus_journey_id) REFERENCES bus_journey(bus_journey_id),
    FOREIGN KEY(start_call_id) REFERENCES bus_call(bus_call_id),
    FOREIGN KEY(end_call_id) REFERENCES bus_call(bus_call_id),
    UNIQUE (bus_leg_id, bus_journey_id)
);

DO $$
BEGIN
    IF (
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_schema = current_schema()
        AND table_name = 'bus_leg'
        AND column_name IN ('board_call_index', 'alight_call_index')
    ) = 2 THEN
        INSERT INTO bus_leg_journey (
            bus_leg_id,
            bus_journey_id,
            start_call_id,
            end_call_id
        )
        SELECT
            bus_leg_id,
            bus_journey_id,
            (
                SELECT bus_call_id
                FROM bus_call
                WHERE call_index = board_call_index
                AND bus_journey_id = bus_leg.bus_journey_id
            ),
            (
                SELECT bus_call_id
                FROM bus_call
                WHERE call_index = alight_call_index
                AND bus_journey_id = bus_leg.bus_journey_id
            )
        FROM bus_leg
        WHERE NOT EXISTS (
            SELECT 1
            FROM bus_leg_journey
            WHERE bus_leg_journey.bus_leg_id = bus_leg.bus_leg_id
            AND bus_leg_journey.bus_journey_id = bus_leg.bus_journey_id
        )
        ON CONFLICT DO NOTHING;
    END IF;
END;
$$;

INSERT INTO bus_leg_journey (
    bus_leg_id,
    bus_journey_id
)
SELECT
    bus_leg_id,
    bus_journey_id
FROM bus_leg
WHERE NOT EXISTS (
    SELECT 1
    FROM bus_leg_journey
    WHERE bus_leg_journey.bus_leg_id = bus_leg_id
    AND bus_leg_journey.bus_journey_id = bus_journey_id
)
ON CONFLICT DO NOTHING;

-- join up bus legs that break over birmingham bus mall ms8 (281514) and square peg (281483)

DO
$$
DECLARE
    v_leg_ids_to_delete INTEGER[];
BEGIN
    SELECT ARRAY_AGG(DISTINCT dep_leg_id)
    INTO v_leg_ids_to_delete
    FROM (
        SELECT
            bus_leg_id AS arr_leg_id,
            bus_call.bus_call_id AS arr_call_id,
            bus_leg_journey.bus_journey_id AS arr_journey_id,
            COALESCE(plan_arr, plan_dep) AS arr
        FROM bus_leg_journey
        INNER JOIN bus_call
        ON bus_leg_journey.end_call_id = bus_call.bus_call_id
        WHERE bus_call.bus_stop_id IN (281514, 281483)
    ) alight
    INNER JOIN (
        SELECT
            bus_leg_id AS dep_leg_id,
            bus_call.bus_call_id AS dep_call_id,
            bus_leg_journey.bus_journey_id AS dep_journey_id,
            plan_dep AS dep
        FROM bus_leg_journey
        INNER JOIN bus_call
        ON bus_leg_journey.start_call_id = bus_call.bus_call_id
        WHERE bus_call.bus_stop_id IN (281514, 281483)
    ) board
    ON (EXTRACT(EPOCH FROM (board.dep - alight.arr))) BETWEEN 0 AND 600
    AND alight.arr_leg_id != board.dep_leg_id
    AND alight.arr_call_id = board.dep_call_id
    WHERE NOT EXISTS (
        SELECT 1
        FROM bus_leg_journey existing
        WHERE existing.bus_leg_id = alight.arr_leg_id
        AND existing.bus_journey_id = board.dep_journey_id
    );

    INSERT INTO bus_leg_journey (
        bus_leg_id,
        bus_journey_id,
        start_call_id,
        end_call_id
    )
    SELECT
        arr_leg_id,
        dep_journey_id,
        dep_start_call_id,
        dep_end_call_id
    FROM (
        SELECT
            bus_leg_id AS arr_leg_id,
            bus_stop_id AS arr_stop_id,
            bus_leg_journey.bus_journey_id AS arr_journey_id,
            COALESCE(plan_arr, plan_dep) AS arr
        FROM bus_leg_journey
        INNER JOIN bus_call
        ON bus_leg_journey.end_call_id = bus_call.bus_call_id
        WHERE bus_call.bus_stop_id IN (281514, 281483)
    ) alight
    INNER JOIN (
        SELECT
            bus_leg_id AS dep_leg_id,
            bus_stop_id AS dep_stop_id,
            bus_leg_journey.start_call_id AS dep_start_call_id,
            bus_leg_journey.end_call_id AS dep_end_call_id,
            bus_leg_journey.bus_journey_id AS dep_journey_id,
            plan_dep AS dep
        FROM bus_leg_journey
        INNER JOIN bus_call
        ON bus_leg_journey.start_call_id = bus_call.bus_call_id
        WHERE bus_call.bus_stop_id IN (281514, 281483)
    ) board
    ON (EXTRACT(EPOCH FROM (board.dep - alight.arr))) BETWEEN 0 AND 600
    AND alight.arr_leg_id != board.dep_leg_id
    AND alight.arr_stop_id = board.dep_stop_id
    WHERE NOT EXISTS (
        SELECT 1
        FROM bus_leg_journey existing
        WHERE existing.bus_leg_id = arr_leg_id
        AND existing.bus_journey_id = dep_journey_id
    )
    ON CONFLICT DO NOTHING;

    DELETE FROM transport_user_bus_leg
    WHERE bus_leg_id = ANY(v_leg_ids_to_delete);

    DELETE FROM bus_leg_journey
    WHERE bus_leg_id = ANY(v_leg_ids_to_delete);

    DELETE FROM bus_leg
    WHERE bus_leg_id = ANY(v_leg_ids_to_delete);
END;
$$;

-- ALTER TABLE bus_leg
-- DROP COLUMN IF EXISTS bus_journey_id;

-- ALTER TABLE bus_leg
-- DROP COLUMN IF EXISTS board_call_index;

-- ALTER TABLE bus_leg
-- DROP COLUMN IF EXISTS alight_call_index;

-- ALTER TABLE bus_call
-- DROP COLUMN IF EXISTS call_index;

DROP FUNCTION IF EXISTS update_bus_leg_vehicle CASCADE;

CREATE OR REPLACE FUNCTION update_bus_leg_vehicle (
    p_bus_leg_id INTEGER_NOTNULL,
    p_bus_vehicle_id INTEGER_NOTNULL
)
RETURNS VOID
LANGUAGE sql
AS
$$
UPDATE busjourney
SET bus_vehicle_id = p_bus_vehicle_id
WHERE bus_journey_id = (
    SELECT bus_journey_id
    FROM busleg
    WHERE bus_leg_id = p_bus_leg_id
);
$$;
CREATE OR REPLACE FUNCTION select_bus_vehicle_details (
    p_operator_id INTEGER,
    p_vehicle_id TEXT_NOTNULL
) RETURNS SETOF bus_vehicle_details
LANGUAGE sql
AS
$$
SELECT
    bus_vehicle_data.bus_vehicle_id,
    bus_vehicle_data.vehicle_operator,
    bus_vehicle_data.vehicle_identifier,
    bus_vehicle_data.bustimes_id,
    bus_vehicle_data.numberplate,
    bus_vehicle_data.bus_model_name,
    bus_vehicle_data.livery_style,
    bus_vehicle_data.vehicle_name
FROM bus_vehicle_data
WHERE
    (p_operator_id IS NULL
    OR (bus_vehicle_data.vehicle_operator).bus_operator_id = p_operator_id)
AND
    (p_vehicle_id IS NULL
    OR bus_vehicle_data.vehicle_identifier = p_vehicle_id);
$$;
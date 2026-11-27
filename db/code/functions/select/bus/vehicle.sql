CREATE OR REPLACE FUNCTION select_bus_vehicle_details (
    p_operator_id INTEGER,
    p_vehicle_id TEXT_NOTNULL
) RETURNS SETOF bus_vehicle_details
LANGUAGE sql
AS
$$
SELECT
    bus_vehicle_details_view.bus_vehicle_id,
    bus_vehicle_details_view.vehicle_operator,
    bus_vehicle_details_view.vehicle_identifier,
    bus_vehicle_details_view.bustimes_id,
    bus_vehicle_details_view.numberplate,
    bus_vehicle_details_view.bus_model_name,
    bus_vehicle_details_view.livery_style,
    bus_vehicle_details_view.vehicle_name
FROM bus_vehicle_details_view
WHERE
    (p_operator_id IS NULL
    OR (bus_vehicle_details_view.vehicle_operator).bus_operator_id = p_operator_id)
AND
    (p_vehicle_id IS NULL
    OR bus_vehicle_details_view.vehicle_identifier = p_vehicle_id);
$$;

CREATE OR REPLACE FUNCTION select_bus_vehicle_details_by_bus_vehicle_id (
    p_bus_vehicle_id INTEGER_NOTNULL
) RETURNS SETOF bus_vehicle_details
LANGUAGE sql
AS
$$
SELECT
    bus_vehicle_details_view.bus_vehicle_id,
    bus_vehicle_details_view.vehicle_operator,
    bus_vehicle_details_view.vehicle_identifier,
    bus_vehicle_details_view.bustimes_id,
    bus_vehicle_details_view.numberplate,
    bus_vehicle_details_view.bus_model_name,
    bus_vehicle_details_view.livery_style,
    bus_vehicle_details_view.vehicle_name
FROM bus_vehicle_details_view
WHERE bus_vehicle_details_view.bus_vehicle_id = p_bus_vehicle_id
$$;
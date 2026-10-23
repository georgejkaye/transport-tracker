CREATE OR REPLACE FUNCTION select_bus_vehicle_user_details_by_user_id (
    p_user_id INTEGER_NOTNULL
) RETURNS SETOF bus_vehicle_user_details
LANGUAGE sql
AS
$$
SELECT
    vehicle_id,
    vehicle_number,
    vehicle_name,
    vehicle_numberplate,
    vehicle_operator,
    vehicle_legs,
    vehicle_duration
FROM bus_vehicle_user_details_view
WHERE user_id = p_user_id
ORDER BY CARDINALITY(vehicle_legs) DESC;
$$;

CREATE OR REPLACE FUNCTION select_bus_vehicle_user_details_by_user_id_and_vehicle_id (
    p_user_id INTEGER_NOTNULL,
    p_vehicle_id INTEGER_NOTNULL
) RETURNS SETOF bus_vehicle_user_details
LANGUAGE sql
AS
$$
SELECT
    vehicle_id,
    vehicle_number,
    vehicle_name,
    vehicle_numberplate,
    vehicle_operator,
    vehicle_legs,
    vehicle_duration
FROM bus_vehicle_user_details_view
WHERE user_id = p_user_id
AND vehicle_id = p_vehicle_id;
$$;
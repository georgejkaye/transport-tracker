DROP FUNCTION IF EXISTS select_bus_models_by_name CASCADE;

CREATE OR REPLACE FUNCTION select_bus_models_by_name (
    p_substring TEXT_NOTNULL
)
RETURNS SETOF bus_model_out_data
LANGUAGE sql
AS
$$
SELECT
    bus_model.bus_model_id,
    bus_model.bus_model_name
FROM bus_model
WHERE LOWER(bus_model.bus_model_name)
LIKE '%' || LOWER(p_substring) || '%';
$$;
DROP FUNCTION IF EXISTS select_bus_models_by_name CASCADE;

CREATE OR REPLACE FUNCTION select_bus_models_by_name (
    p_substring TEXT_NOTNULL
)
RETURNS SETOF bus_model_out_data
LANGUAGE sql
AS
$$
SELECT
    busmodel.bus_model_id,
    busmodel.bus_model_name
FROM busmodel
WHERE LOWER(busmodel.bus_model_name)
LIKE '%' || LOWER(p_substring) || '%';
$$;
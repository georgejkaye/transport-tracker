CREATE OR REPLACE FUNCTION select_bus_operator_details ()
RETURNS SETOF bus_operator_details
LANGUAGE sql
AS
$$
SELECT
    bus_operator_id,
    operator_name,
    national_operator_code,
    bg_colour,
    fg_colour
FROM BusOperator
ORDER BY operator_name ASC;
$$;

CREATE OR REPLACE FUNCTION select_bus_operator_details_by_name (
    p_name TEXT_NOTNULL
) RETURNS SETOF bus_operator_details
LANGUAGE sql
AS
$$
SELECT
    bus_operator_id,
    operator_name,
    national_operator_code,
    bg_colour,
    fg_colour
FROM BusOperator
WHERE LOWER(operator_name) LIKE '%' || LOWER(p_name) || '%'
ORDER BY operator_name ASC;
$$;

CREATE OR REPLACE FUNCTION select_bus_operator_details_by_national_operator_code (
    p_noc TEXT_NOTNULL
) RETURNS SETOF bus_operator_details
LANGUAGE sql
AS
$$
SELECT
    bus_operator_id,
    operator_name,
    national_operator_code,
    bg_colour,
    fg_colour
FROM BusOperator
WHERE LOWER(national_operator_code) = LOWER(p_noc)
ORDER BY operator_name ASC;
$$;
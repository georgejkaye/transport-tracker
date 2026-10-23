CREATE OR REPLACE FUNCTION insert_bus_operators (
    p_operators bus_operator_in_data_notnull[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusOperator (
        operator_name,
        national_operator_code
    ) SELECT
        v_operator.operator_name,
        v_operator.national_operator_code
    FROM UNNEST(p_operators) AS v_operator
    ON CONFLICT DO NOTHING;
END;
$$;
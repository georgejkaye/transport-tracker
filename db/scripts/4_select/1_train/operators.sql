CREATE OR REPLACE FUNCTION select_operator_id_by_name (
    p_operator_name TEXT
)
RETURNS INTEGER
LANGUAGE sql
AS
$$
SELECT operator_id
FROM train_operator
WHERE operator_name;
$$;

CREATE OR REPLACE FUNCTION select_brands_by_operator_code (
    p_operator_code TEXT,
    p_run_date TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF train_brand_out_data
LANGUAGE sql
AS
$$
SELECT
    train_brand.brand_id,
    train_brand.brand_code,
    train_brand.brand_name,
    train_brand.bg_colour,
    train_brand.fg_colour
FROM train_brand
INNER JOIN train_operator
ON train_brand.parent_operator = train_operator.operator_id
WHERE p_operator_code = train_operator.operator_code
AND operation_range @> p_run_date::date
ORDER BY train_brand.brand_name;
$$;
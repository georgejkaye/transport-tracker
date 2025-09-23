DROP FUNCTION select_operator_id_by_name;
DROP FUNCTION select_brands_by_operator_code;
DROP FUNCTION select_operator_by_operator_code;
DROP FUNCTION select_operator_details;

CREATE OR REPLACE FUNCTION select_operator_id_by_name (
    p_operator_name TEXT
)
RETURNS INTEGER
LANGUAGE sql
AS
$$
SELECT train_operator_id
FROM train_operator
WHERE operator_name = p_operator_name;
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
    train_brand.train_brand_id,
    train_brand.brand_code,
    train_brand.brand_name,
    train_brand.bg_colour,
    train_brand.fg_colour
FROM train_brand
INNER JOIN train_operator
ON train_brand.train_operator_id = train_operator.train_operator_id
WHERE p_operator_code = train_operator.operator_code
AND p_run_date::date <@ train_operator.operation_range
ORDER BY train_brand.brand_name;
$$;

CREATE OR REPLACE FUNCTION select_operator_by_operator_code (
    p_operator_code TEXT,
    p_run_date TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF train_operator_out_data
LANGUAGE sql
AS
$$
SELECT
    train_operator.train_operator_id,
    train_operator.operator_code,
    train_operator.operator_name,
    train_operator.bg_colour,
    train_operator.fg_colour,
    train_operator.operation_range,
    COALESCE(train_brand_array.train_brand, ARRAY[]::train_brand_out_data[])
FROM train_operator
LEFT JOIN (
    SELECT
        train_brand.train_operator_id AS train_operator_id,
        ARRAY_AGG((
            train_brand.train_brand_id,
            train_brand.brand_code,
            train_brand.brand_name,
            train_brand.bg_colour,
            train_brand.fg_colour)::train_brand_out_data
            ORDER BY train_brand.brand_name
        ) AS train_brand
    FROM train_brand
    GROUP BY train_brand.train_operator_id
) train_brand_array
ON train_operator.train_operator_id = train_brand_array.train_operator_id
WHERE train_operator.operator_code = p_operator_code
AND train_operator.operation_range @> p_run_date::date;
$$;

CREATE OR REPLACE FUNCTION select_operator_details ()
RETURNS SETOF train_operator_details_out_data
LANGUAGE sql
AS
$$
SELECT
    train_operator.train_operator_id,
    FALSE,
    train_operator.operator_code,
    train_operator.operator_name,
    train_operator.bg_colour,
    train_operator.fg_colour
FROM train_operator
UNION
SELECT
    train_brand.train_brand_id,
    TRUE,
    train_brand.brand_code,
    train_brand.brand_name,
    train_brand.bg_colour,
    train_brand.fg_colour
FROM train_brand;
$$;

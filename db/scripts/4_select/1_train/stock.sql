CREATE OR REPLACE FUNCTION select_operator_stock (
    p_operator_code TEXT,
    p_run_date TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF train_stock_out_data
LANGUAGE sql
AS
$$
SELECT
    train_stock.stock_class,
    train_stock.name AS stock_class_name,
    ARRAY_AGG(
        train_stock_subclass_subtable.stock_subclass
        ORDER BY
            (train_stock_subclass_subtable.stock_subclass).stock_subclass ASC
    )
FROM train_stock
LEFT JOIN (
    SELECT
        train_stock.stock_class,
        (
            train_stock_subclass.stock_subclass,
            train_stock_subclass.name,
            ARRAY_AGG(
                train_stock_formation.cars
                ORDER BY train_stock_formation.cars
            )
        )::train_stock_subclass_out_data AS stock_subclass
    FROM train_stock
    LEFT JOIN train_stock_subclass
    ON train_stock.stock_class = train_stock_subclass.stock_class
    INNER JOIN train_stock_formation
    ON train_stock.stock_class = train_stock_formation.stock_class
    AND (
        train_stock_subclass.stock_subclass IS NULL
        OR train_stock_subclass.stock_subclass
            = train_stock_formation.stock_subclass
    )
    GROUP BY
        train_stock.stock_class,
        train_stock_subclass.stock_subclass,
        train_stock_subclass.name
) train_stock_subclass_subtable
ON train_stock.stock_class = train_stock_subclass_subtable.stock_class
INNER JOIN train_operator_stock
ON train_stock.stock_class = train_operator_stock.stock_class
AND (
    (train_stock_subclass_subtable.stock_subclass).stock_subclass IS NULL
    OR (train_stock_subclass_subtable.stock_subclass).stock_subclass
        = train_operator_stock.stock_subclass
)
INNER JOIN train_operator
ON train_operator_stock.operator_id = train_operator.operator_id
LEFT JOIN train_brand
ON train_operator_stock.brand_id = train_brand.brand_id
WHERE (operator_code = p_operator_code OR brand_code = p_operator_code)
AND p_run_date::date <@ train_operator.operation_range
GROUP BY train_stock.stock_class
ORDER BY train_stock.stock_class ASC;
$$;
CREATE OR REPLACE FUNCTION select_operator_stock (
    p_operator_id INTEGER,
    p_brand_id INTEGER,
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
ON train_operator_stock.train_operator_id = train_operator.train_operator_id
LEFT JOIN train_brand
ON train_operator_stock.train_brand_id = train_brand.train_brand_id
WHERE (
    train_operator.train_operator_id = p_operator_id
    OR train_brand.train_brand_id = p_brand_id
)
AND train_operator.operation_range @> p_run_date::date
GROUP BY train_stock.stock_class
ORDER BY train_stock.stock_class ASC;
$$;
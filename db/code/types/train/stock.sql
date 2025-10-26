DROP TYPE IF EXISTS train_stock_subclass_out_data CASCADE;
DROP TYPE IF EXISTS train_stock_out_data CASCADE;

CREATE TYPE train_stock_subclass_out_data AS (
    stock_subclass INTEGER,
    stock_subclass_name TEXT,
    stock_cars INTEGER_NOTNULL[]
);

CREATE DOMAIN train_stock_subclass_out_data_notnull
AS train_stock_subclass_out_data NOT NULL;

CREATE TYPE train_stock_out_data AS (
    stock_class INTEGER_NOTNULL,
    stock_class_name TEXT,
    stock_subclasses train_stock_subclass_out_data_notnull[]
);

CREATE DOMAIN train_stock_out_data_notnull
AS train_stock_out_data NOT NULL;
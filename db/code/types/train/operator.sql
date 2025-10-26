DROP TYPE IF EXISTS train_brand_out_data CASCADE;
DROP TYPE IF EXISTS train_operator_out_data CASCADE;
DROP TYPE IF EXISTS train_operator_details_out_data CASCADE;

CREATE TYPE train_brand_out_data AS (
    brand_id INTEGER_NOTNULL,
    brand_code TEXT_NOTNULL,
    brand_name TEXT_NOTNULL,
    brand_bg TEXT,
    brand_fg TEXT
);

CREATE DOMAIN train_brand_out_data_notnull
AS train_brand_out_data NOT NULL;

CREATE TYPE train_operator_out_data AS (
    operator_id INTEGER_NOTNULL,
    operator_code TEXT_NOTNULL,
    operator_name TEXT_NOTNULL,
    operator_bg TEXT,
    operator_fg TEXT,
    operation_range DATERANGE_NOTNULL,
    operator_brands train_brand_out_data_notnull[]
);

CREATE DOMAIN train_operator_out_data_notnull
AS train_operator_out_data NOT NULL;

CREATE TYPE train_operator_details_out_data AS (
    operator_id INTEGER_NOTNULL,
    is_brand BOOLEAN_NOTNULL,
    operator_code TEXT_NOTNULL,
    operator_name TEXT_NOTNULL,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE DOMAIN train_operator_details_out_data_notnull
AS train_operator_details_out_data NOT NULL;
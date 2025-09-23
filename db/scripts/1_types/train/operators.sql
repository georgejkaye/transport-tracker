DROP TYPE train_brand_out_data CASCADE;
DROP TYPE train_operator_out_data CASCADE;
DROP TYPE train_operator_details_out_data CASCADE;

CREATE TYPE train_brand_out_data AS (
    brand_id INTEGER,
    brand_code TEXT,
    brand_name TEXT,
    brand_bg TEXT,
    brand_fg TEXT
);

CREATE TYPE train_operator_out_data AS (
    operator_id INTEGER,
    operator_code TEXT,
    operator_name TEXT,
    operator_bg TEXT,
    operator_fg TEXT,
    operation_range DATERANGE,
    operator_brands train_brand_out_data[]
);

CREATE TYPE train_operator_details_out_data AS (
    operator_id INTEGER,
    is_brand BOOLEAN,
    operator_code TEXT,
    operator_name TEXT,
    bg_colour TEXT,
    fg_colour TEXT
);
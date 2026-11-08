DROP TYPE IF EXISTS bus_model_out_data CASCADE;

CREATE TYPE bus_model_out_data AS (
    bus_model_id INTEGER_NOTNULL,
    model_name TEXT_NOTNULL
);

CREATE DOMAIN bus_model_out_data_notnull
AS bus_model_out_data NOT NULL;
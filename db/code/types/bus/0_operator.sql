DROP TYPE IF EXISTS bus_operator_in_data CASCADE;
DROP TYPE IF EXISTS bus_operator_details CASCADE;

DROP DOMAIN IF EXISTS bus_operator_in_data_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_operator_details_notnull CASCADE;

CREATE TYPE bus_operator_in_data AS (
    operator_name TEXT_NOTNULL,
    national_operator_code TEXT_NOTNULL
);

CREATE DOMAIN bus_operator_in_data_notnull
AS bus_operator_in_data NOT NULL;

CREATE TYPE bus_operator_details AS (
    bus_operator_id INTEGER_NOTNULL,
    operator_name TEXT_NOTNULL,
    national_operator_code TEXT_NOTNULL,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE DOMAIN bus_operator_details_notnull
AS bus_operator_details NOT NULL;
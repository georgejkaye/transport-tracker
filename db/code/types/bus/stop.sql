DROP TYPE IF EXISTS bus_stop_in_data CASCADE;
DROP TYPE IF EXISTS bus_stop_details CASCADE;

DROP DOMAIN IF EXISTS bus_stop_in_data_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_stop_details_notnull CASCADE;

CREATE TYPE bus_stop_in_data AS (
    atco_code TEXT_NOTNULL,
    naptan_code TEXT_NOTNULL,
    stop_name TEXT_NOTNULL,
    landmark_name TEXT,
    street_name TEXT_NOTNULL,
    crossing_name TEXT,
    indicator TEXT,
    bearing TEXT_NOTNULL,
    locality_name TEXT_NOTNULL,
    parent_locality_name TEXT,
    grandparent_locality_name TEXT,
    town_name TEXT,
    suburb_name TEXT,
    latitude DECIMAL,
    longitude DECIMAL
);

CREATE DOMAIN bus_stop_in_data_notnull
AS bus_stop_in_data NOT NULL;

CREATE TYPE bus_stop_details AS (
    bus_stop_id INTEGER_NOTNULL,
    atco_code TEXT_NOTNULL,
    naptan_code TEXT_NOTNULL,
    stop_name TEXT_NOTNULL,
    landmark_name TEXT,
    street_name TEXT_NOTNULL,
    crossing_name TEXT,
    indicator TEXT,
    bearing TEXT_NOTNULL,
    locality_name TEXT_NOTNULL,
    parent_locality_name TEXT,
    grandparent_locality_name TEXT,
    town_name TEXT,
    suburb_name TEXT,
    latitude DECIMAL,
    longitude DECIMAL
);

CREATE DOMAIN bus_stop_details_notnull
AS bus_stop_details NOT NULL;
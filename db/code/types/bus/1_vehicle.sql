DROP TYPE IF EXISTS bus_model_in_data CASCADE;
DROP TYPE IF EXISTS bus_vehicle_in_data CASCADE;
DROP TYPE IF EXISTS bus_vehicle_details CASCADE;

DROP DOMAIN IF EXISTS bus_model_in_data_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_vehicle_in_data_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_vehicle_details_notnull CASCADE;

CREATE TYPE bus_model_in_data AS (
    model_name TEXT_NOTNULL
);

CREATE DOMAIN bus_model_in_data_notnull AS bus_model_in_data NOT NULL;

CREATE TYPE bus_vehicle_in_data AS (
    operator_id INTEGER_NOTNULL,
    vehicle_identifier TEXT,
    bustimes_id TEXT,
    vehicle_numberplate TEXT_NOTNULL,
    vehicle_model TEXT,
    vehicle_livery_style TEXT,
    vehicle_name TEXT
);

CREATE DOMAIN bus_vehicle_in_data_notnull AS bus_vehicle_in_data NOT NULL;

CREATE TYPE bus_vehicle_details AS (
    bus_vehicle_id INTEGER_NOTNULL,
    bus_operator bus_operator_details,
    vehicle_identifier TEXT,
    bustimes_id TEXT,
    vehicle_numberplate TEXT_NOTNULL,
    vehicle_model TEXT,
    vehicle_livery_style TEXT,
    vehicle_name TEXT
);

CREATE DOMAIN bus_vehicle_details_notnull AS bus_vehicle_details NOT NULL;
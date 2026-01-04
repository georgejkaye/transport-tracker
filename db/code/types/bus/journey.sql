DROP TYPE IF EXISTS bus_call_in_data CASCADE;
DROP TYPE IF EXISTS bus_journey_in_data CASCADE;
DROP TYPE IF EXISTS bus_journey_service_details CASCADE;
DROP TYPE IF EXISTS bus_call_stop_details CASCADE;
DROP TYPE IF EXISTS bus_journey_call_details CASCADE;
DROP TYPE IF EXISTS bus_journey_details CASCADE;

DROP DOMAIN IF EXISTS bus_call_in_data_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_journey_in_data_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_journey_service_details_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_call_stop_details_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_journey_call_details_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_journey_details_notnull CASCADE;

CREATE TYPE bus_call_in_data AS (
    call_index INTEGER_NOTNULL,
    stop_name TEXT_NOTNULL,
    stop_atco TEXT_NOTNULL,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE
);

CREATE DOMAIN bus_call_in_data_notnull AS bus_call_in_data NOT NULL;

CREATE TYPE bus_journey_in_data AS (
    bustimes_id INTEGER_NOTNULL,
    service_id INTEGER_NOTNULL,
    journey_calls bus_call_in_data[],
    vehicle_id INTEGER
);

CREATE DOMAIN bus_journey_in_data_notnull AS bus_journey_in_data NOT NULL;

CREATE TYPE bus_journey_service_details AS (
    service_id INTEGER_NOTNULL,
    service_operator bus_operator_details,
    service_line TEXT_NOTNULL,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE DOMAIN bus_journey_service_details_notnull AS bus_journey_service_details NOT NULL;

CREATE TYPE bus_call_stop_details AS (
    bus_stop_id BIGINT,
    stop_atco TEXT,
    stop_name TEXT,
    stop_locality TEXT,
    stop_street TEXT,
    stop_indicator TEXT
);

CREATE DOMAIN bus_call_stop_details_notnull AS bus_call_stop_details NOT NULL;

CREATE TYPE bus_journey_call_details AS (
    call_id INTEGER_NOTNULL,
    call_index INT,
    bus_stop bus_call_stop_details,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE
);

CREATE DOMAIN bus_journey_call_details_notnull AS bus_journey_call_details NOT NULL;

CREATE TYPE bus_journey_details AS (
    journey_id INTEGER_NOTNULL,
    journey_service bus_journey_service_details,
    journey_calls bus_journey_call_details[],
    journey_vehicle bus_vehicle_details
);

CREATE DOMAIN bus_journey_details_notnull AS bus_journey_details NOT NULL;
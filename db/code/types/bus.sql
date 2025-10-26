DROP DOMAIN IF EXISTS bus_stop_in_data_notnull CASCADE;
DROP TYPE IF EXISTS bus_stop_in_data CASCADE;
DROP DOMAIN IF EXISTS bus_operator_in_data_notnull CASCADE;
DROP TYPE IF EXISTS bus_operator_in_data CASCADE;
DROP TYPE IF EXISTS bus_service_in_data CASCADE;
DROP TYPE IF EXISTS bus_service_via_in_data CASCADE;
DROP TYPE IF EXISTS bus_model_in_data CASCADE;
DROP TYPE IF EXISTS bus_vehicle_in_data CASCADE;
DROP TYPE IF EXISTS bus_call_in_data CASCADE;
DROP TYPE IF EXISTS bus_journey_in_data CASCADE;
DROP TYPE IF EXISTS bus_leg_in_data CASCADE;

DROP TYPE IF EXISTS bus_stop_details CASCADE;
DROP TYPE IF EXISTS bus_operator_details CASCADE;
DROP TYPE IF EXISTS bus_service_details CASCADE;
DROP TYPE IF EXISTS bus_vehicle_details CASCADE;
DROP TYPE IF EXISTS bus_journey_details CASCADE;
DROP TYPE IF EXISTS bus_journey_service_details CASCADE;
DROP TYPE IF EXISTS bus_call_details CASCADE;
DROP TYPE IF EXISTS bus_call_stop_details CASCADE;
DROP TYPE IF EXISTS bus_journey_call_details CASCADE;
DROP TYPE IF EXISTS bus_leg_service_details CASCADE;
DROP TYPE IF EXISTS bus_leg_user_details CASCADE;
DROP TYPE IF EXISTS bus_vehicle_leg_details CASCADE;
DROP TYPE IF EXISTS bus_vehicle_user_details CASCADE;
DROP TYPE IF EXISTS bus_stop_leg_details CASCADE;
DROP TYPE IF EXISTS bus_stop_user_details CASCADE;

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

CREATE DOMAIN bus_stop_in_data_notnull AS bus_stop_in_data NOT NULL;

CREATE TYPE bus_operator_in_data AS (
    operator_name TEXT_NOTNULL,
    national_operator_code TEXT_NOTNULL
);

CREATE DOMAIN bus_operator_in_data_notnull AS bus_operator_in_data NOT NULL;

CREATE TYPE bus_service_in_data AS (
    service_line TEXT_NOTNULL,
    bods_line_id TEXT_NOTNULL,
    service_operator_national_code TEXT_NOTNULL,
    service_outbound_description TEXT_NOTNULL,
    service_inbound_description TEXT_NOTNULL
);

CREATE DOMAIN bus_service_in_data_notnull AS bus_service_in_data NOT NULL;

CREATE TYPE bus_service_via_in_data AS (
    bods_line_id TEXT_NOTNULL,
    is_outbound BOOLEAN_NOTNULL,
    via_name TEXT_NOTNULL,
    via_index INTEGER_NOTNULL
);

CREATE DOMAIN bus_service_via_in_data_notnull AS bus_service_via_in_data NOT NULL;

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
    bustimes_id TEXT,
    service_id INTEGER_NOTNULL,
    journey_calls bus_call_in_data[],
    vehicle_id INTEGER
);

CREATE DOMAIN bus_journey_in_data_notnull AS bus_journey_in_data NOT NULL;

CREATE TYPE bus_leg_in_data AS (
    journey bus_journey_in_data,
    board_index INTEGER_NOTNULL,
    alight_index INTEGER_NOTNULL
);

CREATE DOMAIN bus_leg_in_data_notnull AS bus_leg_in_data NOT NULL;

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

CREATE DOMAIN bus_stop_details_notnull AS bus_stop_details NOT NULL;

CREATE TYPE bus_operator_details AS (
    bus_operator_id INTEGER_NOTNULL,
    operator_name TEXT_NOTNULL,
    national_operator_code TEXT_NOTNULL,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE DOMAIN bus_operator_details_notnull AS bus_operator_details NOT NULL;

CREATE TYPE bus_service_details AS (
    bus_service_id INTEGER_NOTNULL,
    bus_operator bus_operator_details_notnull,
    service_line TEXT_NOTNULL,
    description_outbound TEXT,
    service_outbound_vias TEXT_NOTNULL[],
    description_inbound TEXT,
    service_inbound_vias TEXT_NOTNULL[],
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE DOMAIN bus_service_details_notnull AS bus_service_details NOT NULL;

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

CREATE TYPE bus_leg_service_details AS (
    service_id INTEGER_NOTNULL,
    service_line TEXT,
    bus_operator bus_operator_details,
    outbound_description TEXT,
    inbound_description TEXT,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE DOMAIN bus_leg_service_details_notnull AS bus_leg_service_details NOT NULL;

CREATE TYPE bus_call_details AS (
    bus_call_id INTEGER_NOTNULL,
    call_index INT,
    bus_stop bus_call_stop_details,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE
);

CREATE DOMAIN bus_call_details_notnull AS bus_call_details NOT NULL;

CREATE TYPE bus_leg_user_details AS (
    leg_id INTEGER_NOTNULL,
    service bus_leg_service_details,
    vehicle bus_vehicle_details,
    calls bus_call_details[],
    duration INTERVAL
);

CREATE DOMAIN bus_leg_user_details_notnull AS bus_leg_user_details NOT NULL;

CREATE TYPE bus_vehicle_leg_details AS (
    leg_id INTEGER_NOTNULL,
    bus_service bus_leg_service_details,
    board_call bus_call_details,
    alight_call bus_call_details,
    duration INTERVAL
);

CREATE DOMAIN bus_vehicle_leg_details_notnull AS bus_vehicle_leg_details NOT NULL;

CREATE TYPE bus_vehicle_user_details AS (
    vehicle_id INTEGER_NOTNULL,
    identifier TEXT,
    name TEXT,
    numberplate TEXT,
    operator bus_operator_details,
    legs bus_vehicle_leg_details[],
    duration INTERVAL
);

CREATE DOMAIN bus_vehicle_user_details_notnull AS bus_vehicle_user_details NOT NULL;

CREATE TYPE bus_stop_leg_details AS (
    leg_id INTEGER_NOTNULL,
    bus_service bus_leg_service_details,
    board_call bus_call_details,
    alight_call bus_call_details,
    this_call bus_call_details,
    stops_before INT,
    stops_after INT
);

CREATE DOMAIN bus_stop_leg_details_notnull AS bus_stop_leg_details NOT NULL;

CREATE TYPE bus_stop_user_details AS (
    stop_id INTEGER_NOTNULL,
    atco_code TEXT,
    naptan_code TEXT,
    stop_name TEXT,
    landmark_name TEXT,
    street_name TEXT,
    crossing_name TEXT,
    indicator TEXT,
    bearing TEXT,
    locality_name TEXT,
    parent_locality_name TEXT,
    grandparent_locality_name TEXT,
    town_name TEXT,
    suburb_name TEXT,
    latitude DECIMAL,
    longitude DECIMAL,
    stop_legs bus_stop_leg_details[]
);

CREATE DOMAIN bus_stop_user_details_notnull AS bus_stop_user_details NOT NULL;
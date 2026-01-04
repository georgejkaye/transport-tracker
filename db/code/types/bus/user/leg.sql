DROP TYPE IF EXISTS bus_leg_service_details CASCADE;
DROP TYPE IF EXISTS bus_call_details CASCADE;
DROP TYPE IF EXISTS bus_leg_user_details CASCADE;

DROP TYPE IF EXISTS insert_bus_leg_result CASCADE;

DROP DOMAIN IF EXISTS bus_leg_service_details_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_call_details_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_leg_user_details_notnull CASCADE;

CREATE TYPE bus_leg_service_details AS (
    service_id INTEGER_NOTNULL,
    service_line TEXT,
    bus_operator bus_operator_details,
    outbound_description TEXT,
    inbound_description TEXT,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE DOMAIN bus_leg_service_details_notnull
AS bus_leg_service_details NOT NULL;

CREATE TYPE bus_call_details AS (
    bus_call_id INTEGER_NOTNULL,
    call_index INT,
    bus_stop bus_call_stop_details,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE
);

CREATE DOMAIN bus_call_details_notnull
AS bus_call_details NOT NULL;

CREATE TYPE bus_leg_user_details AS (
    leg_id INTEGER_NOTNULL,
    service bus_leg_service_details,
    vehicle bus_vehicle_details,
    calls bus_call_details[],
    duration INTERVAL
);

CREATE DOMAIN bus_leg_user_details_notnull
AS bus_leg_user_details NOT NULL;

CREATE TYPE insert_bus_leg_result AS (
    bus_leg_id INTEGER_NOTNULL
);
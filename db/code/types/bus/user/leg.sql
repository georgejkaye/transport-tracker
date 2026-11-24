DROP TYPE IF EXISTS bus_leg_service_details CASCADE;
DROP TYPE IF EXISTS bus_call_details CASCADE;
DROP TYPE IF EXISTS bus_leg_journey_summary CASCADE;
DROP TYPE IF EXISTS bus_leg_journey_stop_summary CASCADE;
DROP TYPE IF EXISTS bus_leg_user_details CASCADE;
DROP TYPE IF EXISTS bus_leg_summary CASCADE;

DROP TYPE IF EXISTS insert_bus_leg_result CASCADE;

DROP DOMAIN IF EXISTS bus_leg_service_details_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_call_details_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_leg_journey_summary_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_leg_journey_stop_summary_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_leg_user_details_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_leg_summary_notnull CASCADE;

CREATE TYPE bus_leg_service_details AS (
    service_id INTEGER_NOTNULL,
    line TEXT,
    operator bus_operator_summary,
    outbound_description TEXT,
    inbound_description TEXT
);

CREATE DOMAIN bus_leg_service_details_notnull
AS bus_leg_service_details NOT NULL;

CREATE TYPE bus_call_details AS (
    bus_call_id INTEGER_NOTNULL,
    stop bus_call_stop_details,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE
);

CREATE DOMAIN bus_call_details_notnull
AS bus_call_details NOT NULL;

CREATE TYPE bus_leg_journey_stop_summary AS (
    stop_id INTEGER_NOTNULL,
    name TEXT_NOTNULL,
    locality TEXT,
    indicator TEXT
);

CREATE DOMAIN bus_leg_journey_stop_summary_notnull
AS bus_leg_journey_stop_summary NOT NULL;

CREATE TYPE bus_leg_journey_summary AS (
    journey_id INTEGER_NOTNULL,
    service_id INTEGER_NOTNULL,
    line TEXT_NOTNULL,
    journey_start bus_leg_journey_stop_summary,
    journey_end bus_leg_journey_stop_summary,
    leg_start bus_leg_journey_stop_summary,
    leg_end bus_leg_journey_stop_summary
);

CREATE DOMAIN bus_leg_journey_summary_notnull
AS bus_leg_journey_summary NOT NULL;

CREATE TYPE bus_leg_summary AS (
    leg_id INTEGER_NOTNULL,
    operator bus_operator_summary,
    journeys bus_leg_journey_summary[],
    vehicle bus_vehicle_details,
    calls bus_call_details[],
    duration INTERVAL
);

CREATE DOMAIN bus_leg_summary_notnull
AS bus_leg_summary NOT NULL;

CREATE TYPE insert_bus_leg_result AS (
    bus_leg_id INTEGER_NOTNULL
);
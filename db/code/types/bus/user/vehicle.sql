DROP TYPE IF EXISTS bus_vehicle_leg_details CASCADE;
DROP TYPE IF EXISTS bus_vehicle_user_details CASCADE;

DROP DOMAIN IF EXISTS bus_vehicle_leg_details_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_vehicle_user_details_notnull CASCADE;

CREATE TYPE bus_vehicle_leg_details AS (
    leg_id INTEGER_NOTNULL,
    operator bus_operator_summary,
    journeys bus_leg_journey_summary[],
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
    operator bus_operator_summary,
    legs bus_vehicle_leg_details[],
    duration INTERVAL
);

CREATE DOMAIN bus_vehicle_user_details_notnull AS bus_vehicle_user_details NOT NULL;
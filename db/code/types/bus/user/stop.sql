DROP TYPE IF EXISTS bus_stop_leg_details CASCADE;
DROP TYPE IF EXISTS bus_stop_user_details CASCADE;

DROP DOMAIN IF EXISTS bus_stop_leg_details_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_stop_user_details_notnull CASCADE;

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

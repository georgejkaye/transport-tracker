DROP TYPE IF EXISTS transport_user_bus_stop_leg_summary CASCADE;
DROP TYPE IF EXISTS transport_user_bus_stop_details CASCADE;
DROP TYPE IF EXISTS transport_user_bus_stop_summary CASCADE;

DROP DOMAIN IF EXISTS transport_user_bus_stop_leg_summary_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_bus_stop_details_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_bus_stop_summary_notnull CASCADE;

CREATE TYPE transport_user_bus_stop_leg_summary
AS (
    leg_id INTEGER_NOTNULL,
    operator bus_operator_summary,
    services bus_service_summary[],
    board_call bus_call_details,
    alight_call bus_call_details,
    this_call bus_call_details,
    stops_before INT,
    stops_after INT
);

CREATE DOMAIN transport_user_bus_stop_leg_summary_notnull
AS transport_user_bus_stop_leg_summary NOT NULL;

CREATE TYPE transport_user_bus_stop_details
AS (
    stop_id INTEGER_NOTNULL,
    atco_code TEXT,
    naptan_code TEXT,
    stop_name TEXT,
    landmark_name TEXT,
    street_name TEXT,
    indicator TEXT,
    bearing TEXT,
    locality_name TEXT,
    town_name TEXT,
    latitude DECIMAL,
    longitude DECIMAL,
    stop_legs transport_user_bus_stop_leg_summary[]
);

CREATE DOMAIN transport_user_bus_stop_details_notnull
AS transport_user_bus_stop_details NOT NULL;

CREATE TYPE transport_user_bus_stop_summary AS (
    stop_id INTEGER_NOTNULL,
    atco_code TEXT,
    naptan_code TEXT,
    stop_name TEXT,
    landmark_name TEXT,
    street_name TEXT,
    indicator TEXT,
    bearing TEXT,
    locality_name TEXT,
    town_name TEXT,
    latitude DECIMAL,
    longitude DECIMAL,
    boards BIGINT_NOTNULL,
    alights BIGINT_NOTNULL,
    calls BIGINT_NOTNULL
);

CREATE DOMAIN transport_user_bus_stop_summary_notnull
AS transport_user_bus_stop_summary NOT NULL;

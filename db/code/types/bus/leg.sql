DROP TYPE IF EXISTS bus_leg_in_data CASCADE;

DROP DOMAIN IF EXISTS bus_leg_in_data_notnull CASCADE;

CREATE TYPE bus_leg_in_data AS (
    journey bus_journey_in_data,
    board_index INTEGER_NOTNULL,
    alight_index INTEGER_NOTNULL
);

CREATE DOMAIN bus_leg_in_data_notnull AS bus_leg_in_data NOT NULL;
DROP TYPE IF EXISTS bus_leg_in_data CASCADE;
DROP TYPE IF EXISTS bus_leg_journey_in_data CASCADE;

DROP DOMAIN IF EXISTS bus_leg_in_data_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_leg_journey_in_data_notnull CASCADE;

CREATE TYPE bus_leg_journey_in_data AS (
    journey bus_journey_in_data_notnull,
    start_atco TEXT_NOTNULL,
    start_time TIMESTAMP_NOTNULL,
    end_atco TEXT_NOTNULL,
    end_time TIMESTAMP_NOTNULL
);

CREATE DOMAIN bus_leg_journey_in_data_notnull
AS bus_leg_journey_in_data NOT NULL;

CREATE TYPE bus_leg_in_data AS (
    journeys bus_leg_journey_in_data_notnull[],
    board_atco TEXT_NOTNULL,
    alight_atco TEXT_NOTNULL
);

CREATE DOMAIN bus_leg_in_data_notnull
AS bus_leg_in_data NOT NULL;
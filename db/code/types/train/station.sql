DROP TYPE IF EXISTS train_station_name_point_in_data CASCADE;
DROP TYPE IF EXISTS train_station_out_data CASCADE;
DROP TYPE IF EXISTS train_station_leg_names_in_data CASCADE;
DROP TYPE IF EXISTS train_station_point_out_data CASCADE;
DROP TYPE IF EXISTS train_station_points_out_data CASCADE;
DROP TYPE IF EXISTS train_station_leg_points_out_data CASCADE;

CREATE TYPE train_station_name_point_in_data AS (
    station_name TEXT_NOTNULL,
    platform TEXT
);

CREATE DOMAIN train_station_name_point_in_data_notnull
AS train_station_name_point_in_data NOT NULL;

CREATE TYPE train_station_out_data AS (
    station_id INTEGER_NOTNULL,
    station_crs TEXT_NOTNULL,
    station_name TEXT_NOTNULL,
    operator_id INTEGER_NOTNULL,
    brand_id INTEGER
);

CREATE DOMAIN train_station_out_data_notnull
AS train_station_out_data NOT NULL;

CREATE TYPE train_station_leg_names_in_data AS (
    station_names TEXT_NOTNULL[]
);

CREATE DOMAIN train_station_leg_names_in_data_notnull
AS train_station_leg_names_in_data NOT NULL;

CREATE TYPE train_station_point_out_data AS (
    platform TEXT,
    latitude DECIMAL_NOTNULL,
    longitude DECIMAL_NOTNULL
);

CREATE DOMAIN train_station_point_out_data_notnull
AS train_station_point_out_data NOT NULL;

CREATE TYPE train_station_points_out_data AS (
    station_id INTEGER_NOTNULL,
    station_crs TEXT_NOTNULL,
    station_name TEXT_NOTNULL,
    search_name TEXT_NOTNULL,
    platform_points train_station_point_out_data_notnull[]
);

CREATE DOMAIN train_station_points_out_data_notnull
AS train_station_points_out_data NOT NULL;

CREATE TYPE train_station_leg_points_out_data AS (
    leg_stations train_station_points_out_data_notnull[]
);

CREATE DOMAIN train_station_leg_points_out_data_notnull
AS train_station_leg_points_out_data NOT NULL;
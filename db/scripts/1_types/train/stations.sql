DROP TYPE train_station_name_point_in_data CASCADE;
DROP TYPE train_station_out_data CASCADE;
DROP TYPE train_station_leg_names_in_data CASCADE;
DROP TYPE train_station_point_out_data CASCADE;
DROP TYPE train_station_points_out_data CASCADE;
DROP TYPE train_station_leg_points_out_data CASCADE;

CREATE TYPE train_station_name_point_in_data AS (
    station_name TEXT,
    platform TEXT
);

CREATE TYPE train_station_out_data AS (
    station_id INTEGER,
    station_crs TEXT,
    station_name TEXT,
    operator_id INTEGER,
    brand_id INTEGER
);

CREATE TYPE train_station_leg_names_in_data AS (
    station_names TEXT[]
);

CREATE TYPE train_station_point_out_data AS (
    platform TEXT,
    latitude NUMERIC,
    longitude NUMERIC
);

CREATE TYPE train_station_points_out_data AS (
    station_id INTEGER,
    station_crs TEXT,
    station_name TEXT,
    search_name TEXT,
    platform_points train_station_point_out_data[]
);

CREATE TYPE train_station_leg_points_out_data AS (
    leg_stations train_station_points_out_data[]
);
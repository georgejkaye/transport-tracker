DROP TYPE train_station_point_in_data CASCADE;
DROP TYPE train_station_out_data CASCADE;
DROP TYPE train_station_point_out_data CASCADE;

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

CREATE TYPE train_station_point_out_data AS (
    station_id INTEGER,
    station_crs TEXT,
    station_name TEXT,
    platform TEXT,
    latitude NUMERIC,
    longitude NUMERIC
);
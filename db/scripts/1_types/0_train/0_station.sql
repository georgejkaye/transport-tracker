DROP TYPE train_station_out_data CASCADE;

CREATE TYPE train_station_out_data AS (
    station_id INTEGER,
    station_crs TEXT,
    station_name TEXT,
    operator_id INTEGER,
    brand_id INTEGER
);
DROP TYPE IF EXISTS transport_user_train_leg_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_train_leg_operator_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_train_leg_station_out_data CASCADE;

CREATE TYPE transport_user_train_leg_station_out_data AS (
    station_id INTEGER,
    station_crs TEXT,
    station_name TEXT
);

CREATE DOMAIN transport_user_train_leg_station_out_data_notnull
AS transport_user_train_leg_station_out_data NOT NULL;

CREATE TYPE transport_user_train_leg_operator_out_data AS (
    operator_id INTEGER,
    operator_code TEXT,
    operator_name TEXT
);

CREATE DOMAIN transport_user_train_leg_operator_out_data_notnull
AS transport_user_train_leg_operator_out_data NOT NULL;

CREATE TYPE transport_user_train_leg_out_data AS (
    leg_id INTEGER,
    origin transport_user_train_leg_station_out_data,
    destination transport_user_train_leg_station_out_data,
    start_datetime TIMESTAMP WITH TIME ZONE,
    operator train_leg_operator_out_data,
    brand train_leg_operator_out_data,
    distance DECIMAL,
    duration INTERVAL,
    delay INTEGER
);

CREATE DOMAIN transport_user_train_leg_out_data_notnull
AS transport_user_train_leg_out_data NOT NULL;
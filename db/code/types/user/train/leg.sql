DROP TYPE IF EXISTS transport_user_train_leg_out_data CASCADE;

CREATE TYPE transport_user_train_leg_out_data AS (
    leg_id INTEGER,
    board_station train_station_high_out_data_notnull,
    alight_station train_station_high_out_data_notnull,
    start_datetime TIMESTAMP WITH TIME ZONE,
    operator train_operator_high_out_data_notnull,
    brand train_operator_high_out_data,
    distance DECIMAL,
    duration INTERVAL,
    delay INTEGER
);

CREATE DOMAIN transport_user_train_leg_out_data_notnull
AS transport_user_train_leg_out_data NOT NULL;
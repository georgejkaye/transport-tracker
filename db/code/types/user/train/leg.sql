DROP TYPE IF EXISTS transport_user_train_leg_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_train_leg_stats CASCADE;

CREATE TYPE transport_user_train_leg_out_data AS (
    leg_id INTEGER_NOTNULL,
    board_station train_station_high_out_data_notnull,
    alight_station train_station_high_out_data_notnull,
    start_datetime TIMESTAMP_NOTNULL,
    operator train_operator_high_out_data_notnull,
    brand train_operator_high_out_data,
    distance DECIMAL,
    duration INTERVAL,
    delay INTEGER
);

CREATE DOMAIN transport_user_train_leg_out_data_notnull
AS transport_user_train_leg_out_data NOT NULL;

CREATE TYPE transport_user_train_leg_stats AS (
    count INTEGER_NOTNULL,
    total_distance DECIMAL_NOTNULL,
    longest_distance DECIMAL_NOTNULL,
    shortest_distance DECIMAL_NOTNULL,
    total_duration INTERVAL_NOTNULL,
    longest_duration INTERVAL_NOTNULL,
    shortest_duration INTERVAL_NOTNULL,
    total_delay INTEGER_NOTNULL,
    longest_delay INTEGER_NOTNULL,
    shortest_delay INTEGER_NOTNULL
);
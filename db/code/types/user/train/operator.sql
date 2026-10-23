DROP TYPE IF EXISTS transport_user_train_operator_train_leg_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_operator_train_leg_out_data_notnull CASCADE;
DROP TYPE IF EXISTS transport_user_train_operator_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_operator_out_data_notnull CASCADE;
DROP TYPE IF EXISTS transport_user_train_operator_high_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_operator_high_out_data_notnull CASCADE;
DROP TYPE IF EXISTS transport_user_train_operator_stats CASCADE;

CREATE TYPE transport_user_train_operator_train_leg_out_data AS (
    train_leg_id INTEGER_NOTNULL,
    board_station train_station_high_out_data_notnull,
    alight_station train_station_high_out_data_notnull,
    start_datetime TIMESTAMP_NOTNULL,
    distance DECIMAL,
    duration INTERVAL_NOTNULL,
    delay INTEGER
);

CREATE DOMAIN transport_user_train_operator_train_leg_out_data_notnull
AS transport_user_train_operator_train_leg_out_data NOT NULL;

CREATE TYPE transport_user_train_operator_out_data AS (
    train_operator_id INTEGER_NOTNULL,
    operator_code TEXT_NOTNULL,
    operator_name TEXT_NOTNULL,
    leg_count INTEGER_NOTNULL,
    leg_duration INTERVAL_NOTNULL,
    leg_distance DECIMAL_NOTNULL,
    leg_delay INTEGER_NOTNULL,
    operator_legs transport_user_train_operator_train_leg_out_data_notnull[]
);

CREATE DOMAIN transport_user_train_operator_out_data_notnull
AS transport_user_train_operator_out_data NOT NULL;

CREATE TYPE transport_user_train_operator_high_out_data AS (
    train_operator_id INTEGER_NOTNULL,
    operator_code TEXT_NOTNULL,
    operator_name TEXT_NOTNULL,
    is_brand BOOLEAN_NOTNULL,
    leg_count INTEGER_NOTNULL,
    leg_duration INTERVAL_NOTNULL,
    leg_distance DECIMAL_NOTNULL,
    leg_delay INTEGER_NOTNULL
);

CREATE DOMAIN transport_user_train_operator_high_out_data_notnull
AS transport_user_train_operator_high_out_data NOT NULL;
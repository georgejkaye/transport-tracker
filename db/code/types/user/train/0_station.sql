DROP TYPE IF EXISTS transport_user_train_station_leg_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_station_leg_out_data_notnull CASCADE;
DROP TYPE IF EXISTS transport_user_train_station_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_station_out_data_notnull CASCADE;
DROP TYPE IF EXISTS transport_user_train_station_high_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_station_high_out_data_notnull CASCADE;

CREATE TYPE transport_user_train_station_leg_out_data AS (
    leg_id INTEGER_NOTNULL,
    board_station train_station_high_out_data_notnull,
    alight_station train_station_high_out_data_notnull,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    operator train_operator_high_out_data_notnull,
    brand train_operator_high_out_data,
    call_index INTEGER_NOTNULL,
    calls_before INTEGER_NOTNULL,
    calls_after INTEGER_NOTNULL
);

CREATE DOMAIN transport_user_train_station_leg_out_data_notnull
AS transport_user_train_station_leg_out_data NOT NULL;

CREATE TYPE transport_user_train_station_out_data AS (
    station_id INTEGER_NOTNULL,
    station_crs TEXT_NOTNULL,
    station_name TEXT_NOTNULL,
    station_operator train_operator_high_out_data_notnull,
    station_brand train_operator_high_out_data,
    boards BIGINT_NOTNULL,
    alights BIGINT_NOTNULL,
    calls BIGINT_NOTNULL,
    station_legs transport_user_train_station_leg_out_data_notnull[]
);

CREATE DOMAIN transport_user_train_station_out_data_notnull
AS transport_user_train_station_out_data NOT NULL;

CREATE TYPE transport_user_train_station_high_out_data AS (
    station_id INTEGER_NOTNULL,
    station_crs TEXT_NOTNULL,
    station_name TEXT_NOTNULL,
    station_operator train_operator_high_out_data_notnull,
    station_brand train_operator_high_out_data,
    boards BIGINT_NOTNULL,
    alights BIGINT_NOTNULL,
    calls BIGINT_NOTNULL
);

CREATE DOMAIN transport_user_train_station_high_out_data_notnull
AS transport_user_train_station_high_out_data NOT NULL;
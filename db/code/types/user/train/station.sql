DROP TYPE IF EXISTS transport_user_train_station_operator_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_train_station_leg_endpoint_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_train_station_leg_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_train_station_out_data CASCADE;

CREATE TYPE transport_user_train_station_operator_out_data AS (
    operator_id INTEGER_NOTNULL,
    operator_code TEXT_NOTNULL,
    operator_name TEXT_NOTNULL
);

CREATE DOMAIN transport_user_train_station_operator_out_data_notnull
AS transport_user_train_station_operator_out_data NOT NULL;

CREATE TYPE transport_user_train_station_leg_endpoint_out_data AS (
    station_id INTEGER_NOTNULL,
    station_crs TEXT_NOTNULL,
    station_name TEXT_NOTNULL
);

CREATE DOMAIN transport_user_train_station_leg_endpoint_out_data_notnull
AS transport_user_train_station_leg_endpoint_out_data NOT NULL;

CREATE TYPE transport_user_train_station_leg_out_data AS (
    leg_id INTEGER_NOTNULL,
    board_station transport_user_train_station_leg_endpoint_out_data_notnull,
    alight_station transport_user_train_station_leg_endpoint_out_data_notnull,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    leg_operator transport_user_train_station_operator_out_data_notnull,
    leg_brand transport_user_train_station_operator_out_data,
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
    station_operator transport_user_train_station_operator_out_data,
    station_brand transport_user_train_station_operator_out_data,
    boards INTEGER_NOTNULL,
    alights INTEGER_NOTNULL,
    calls INTEGER_NOTNULL,
    station_legs transport_user_train_station_leg_out_data_notnull[]
);

CREATE DOMAIN transport_user_train_station_out_data_notnull
AS transport_user_train_station_out_data NOT NULL;
DROP TYPE IF EXISTS transport_user_train_station_operator_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_train_station_leg_endpoint_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_train_station_leg_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_train_station_out_data CASCADE;

CREATE TYPE transport_user_train_station_operator_out_data AS (
    operator_id INTEGER,
    operator_code TEXT,
    operator_name TEXT
);

CREATE DOMAIN transport_user_train_station_operator_out_data_notnull
AS transport_user_train_station_operator_out_data NOT NULL;

CREATE TYPE transport_user_train_station_leg_endpoint_out_data AS (
    station_id INTEGER,
    station_crs TEXT,
    station_name TEXT
);

CREATE DOMAIN transport_user_train_station_leg_endpoint_out_data_notnull
AS transport_user_train_station_leg_endpoint_out_data NOT NULL;

CREATE TYPE transport_user_train_station_leg_out_data AS (
    leg_id INTEGER,
    board_station transport_user_train_station_leg_endpoint_out_data,
    alight_station transport_user_train_station_leg_endpoint_out_data,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    leg_operator transport_user_train_station_operator_out_data,
    leg_brand transport_user_train_station_operator_out_data,
    call_index INTEGER,
    calls_before INTEGER,
    calls_after INTEGER
);

CREATE DOMAIN transport_user_train_station_leg_out_data_notnull
AS transport_user_train_station_leg_out_data NOT NULL;

CREATE TYPE transport_user_train_station_out_data AS (
    station_id INTEGER,
    station_crs TEXT,
    station_name TEXT,
    boards INTEGER,
    alights INTEGER,
    calls INTEGER,
    station_operator transport_user_train_station_operator_out_data,
    station_brand transport_user_train_station_operator_out_data,
    station_legs transport_user_train_station_leg_out_data[]
);

CREATE DOMAIN transport_user_train_station_out_data_notnull
AS transport_user_train_station_out_data NOT NULL;
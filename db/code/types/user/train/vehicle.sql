DROP TYPE IF EXISTS transport_user_train_leg_unit_segment_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_leg_unit_segment_out_data_notnull CASCADE;
DROP TYPE IF EXISTS transport_user_train_class_leg_unit_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_class_leg_unit_out_data_notnull CASCADE;
DROP TYPE IF EXISTS transport_user_train_class_leg_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_class_leg_out_data_notnull CASCADE;
DROP TYPE IF EXISTS transport_user_train_class_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_class_out_data_notnull CASCADE;
DROP TYPE IF EXISTS transport_user_train_class_high_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_class_high_out_data_notnull CASCADE;
DROP TYPE IF EXISTS transport_user_train_unit_leg_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_unit_leg_out_data_notnull CASCADE;
DROP TYPE IF EXISTS transport_user_train_unit_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_unit_out_data_notnull CASCADE;
DROP TYPE IF EXISTS transport_user_train_unit_high_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_unit_high_out_data_notnull CASCADE;

CREATE TYPE transport_user_train_leg_unit_segment_out_data AS (
    start_station train_leg_station_out_data_notnull,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    end_station train_leg_station_out_data_notnull,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE
);

CREATE DOMAIN transport_user_train_leg_unit_segment_out_data_notnull
AS transport_user_train_leg_unit_segment_out_data NOT NULL;

CREATE TYPE transport_user_train_class_leg_unit_out_data AS (
    stock_number INTEGER,
    stock_subclass INTEGER,
    stock_cars INTEGER,
    segments transport_user_train_leg_unit_segment_out_data_notnull[],
    duration INTERVAL,
    distance DECIMAL
);

CREATE DOMAIN transport_user_train_class_leg_unit_out_data_notnull
AS transport_user_train_class_leg_unit_out_data NOT NULL;

CREATE TYPE transport_user_train_class_leg_out_data AS (
    leg_id INTEGER_NOTNULL,
    leg_start TIMESTAMP_NOTNULL,
    board train_leg_station_out_data_notnull,
    alight train_leg_station_out_data_notnull,
    operator train_leg_operator_out_data,
    brand train_leg_operator_out_data,
    units transport_user_train_class_leg_unit_out_data_notnull[],
    distance DECIMAL,
    duration INTERVAL
);

CREATE DOMAIN transport_user_train_class_leg_out_data_notnull
AS transport_user_train_class_leg_out_data NOT NULL;


CREATE TYPE transport_user_train_class_out_data AS (
    class_no INTEGER_NOTNULL,
    class_name TEXT,
    class_count INTEGER_NOTNULL,
    distance DECIMAL,
    duration INTERVAL_NOTNULL,
    class_legs transport_user_train_class_leg_out_data_notnull[]
);

CREATE DOMAIN transport_user_train_class_out_data_notnull
AS transport_user_train_class_out_data NOT NULL;

CREATE TYPE transport_user_train_class_high_out_data AS (
    class_no INTEGER_NOTNULL,
    class_name TEXT,
    class_count INTEGER_NOTNULL,
    distance DECIMAL,
    duration INTERVAL_NOTNULL
);

CREATE DOMAIN transport_user_train_class_high_out_data_notnull
AS transport_user_train_class_high_out_data NOT NULL;

CREATE TYPE transport_user_train_unit_leg_out_data AS (
    leg_id INTEGER_NOTNULL,
    leg_start TIMESTAMP_NOTNULL,
    segments transport_user_train_leg_unit_segment_out_data_notnull[],
    distance DECIMAL,
    duration INTERVAL,
    leg_board_station train_leg_station_out_data_notnull,
    leg_alight_station train_leg_station_out_data_notnull,
    operator train_leg_operator_out_data,
    brand train_leg_operator_out_data
);

CREATE TYPE transport_user_train_unit_out_data AS (
    unit_number INTEGER_NOTNULL,
    unit_class INTEGER_NOTNULL,
    unit_subclass INTEGER,
    unit_cars INTEGER,
    unit_count INTEGER_NOTNULL,
    distance DECIMAL,
    duration INTERVAL_NOTNULL,
    unit_legs transport_user_train_unit_leg_out_data[]
);

CREATE DOMAIN transport_user_train_unit_out_data_notnull
AS transport_user_train_unit_out_data NOT NULL;

CREATE TYPE transport_user_train_unit_high_out_data AS (
    unit_number INTEGER_NOTNULL,
    unit_class INTEGER_NOTNULL,
    unit_subclass INTEGER,
    unit_cars INTEGER,
    unit_count INTEGER_NOTNULL,
    distance DECIMAL,
    duration INTERVAL_NOTNULL
);

CREATE DOMAIN transport_user_train_unit_high_out_data_notnull
AS transport_user_train_unit_high_out_data NOT NULL;
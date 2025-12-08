DROP TYPE IF EXISTS transport_user_train_class_leg_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_class_leg_out_data_notnull CASCADE;
DROP TYPE IF EXISTS transport_user_train_class_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_class_out_data_notnull CASCADE;

CREATE TYPE transport_user_train_class_leg_out_data AS (
    leg_id INTEGER_NOTNULL,
    unit_number INTEGER,
    stock_subclass INTEGER,
    stock_cars INTEGER,
    stock_start_station train_leg_station_out_data_notnull,
    stock_end_station train_leg_station_out_data_notnull,
    distance DECIMAL,
    duration INTERVAL,
    leg_board_station train_leg_station_out_data_notnull,
    leg_alight_station train_leg_station_out_data_notnull,
    operator train_leg_operator_out_data,
    brand train_leg_operator_out_data
);

CREATE DOMAIN transport_user_train_class_leg_out_data_notnull
AS transport_user_train_class_leg_out_data NOT NULL;


CREATE TYPE transport_user_train_class_out_data AS (
    class_no INTEGER_NOTNULL,
    class_name TEXT_NOTNULL,
    class_legs transport_user_train_class_leg_out_data_notnull[]
);

CREATE DOMAIN transport_user_train_class_out_data_notnull
AS transport_user_train_class_out_data NOT NULL;
DROP TYPE IF EXISTS transport_user_train_class_leg_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_class_leg_out_data_notnull CASCADE;
DROP TYPE IF EXISTS transport_user_train_class_out_data CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_class_out_data_notnull CASCADE;

CREATE TYPE transport_user_train_class_leg_out_data AS (
    leg_id INTEGER_NOTNULL,
    board_station transport_user_train_station_leg_endpoint_out_data_notnull,
    alight_station transport_user_train_station_leg_endpoint_out_data_notnull,
    unit_no INTEGER_NOTNULL,
    distance DECIMAL_NOTNULL,
    duration INTERVAL_NOTNULL
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
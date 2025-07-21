DROP TYPE train_leg_call_in_data CASCADE;
DROP TYPE train_leg_in_data CASCADE;

DROP TYPE transport_user_train_leg_station_out_data CASCADE;
DROP TYPE transport_user_train_leg_operator_out_data CASCADE;
DROP TYPE transport_user_train_leg_station_out_data CASCADE;
DROP TYPE transport_user_train_leg_associated_service_out_data CASCADE;
DROP TYPE transport_user_train_leg_service_out_data CASCADE;

CREATE TYPE train_leg_call_in_data AS (
    station_crs TEXT,
    arr_call_service_uid TEXT,
    arr_call_service_run_date TIMESTAMP WITH TIME ZONE,
    arr_call_plan_arr TIMESTAMP WITH TIME ZONE,
    arr_call_act_arr TIMESTAMP WITH TIME ZONE,
    arr_call_plan_dep TIMESTAMP WITH TIME ZONE,
    arr_call_act_dep TIMESTAMP WITH TIME ZONE,
    dep_call_service_uid TEXT,
    dep_call_service_run_date TIMESTAMP WITH TIME ZONE,
    dep_call_plan_arr TIMESTAMP WITH TIME ZONE,
    dep_call_act_arr TIMESTAMP WITH TIME ZONE,
    dep_call_plan_dep TIMESTAMP WITH TIME ZONE,
    dep_call_act_dep TIMESTAMP WITH TIME ZONE,
    mileage DECIMAL,
    associated_type_id INTEGER
);

CREATE TYPE train_leg_in_data AS (
    leg_services train_service_in_data[],
    service_endpoints train_service_endpoint_in_data[],
    service_calls train_call_in_data[],
    service_associations train_associated_service_in_data[],
    leg_calls train_leg_call_in_data[],
    leg_stock train_stock_segment_in_data[],
    leg_distance DECIMAL
);


CREATE TYPE transport_user_train_leg_station_out_data AS (
    crs TEXT,
    name TEXT
);

CREATE TYPE transport_user_train_leg_operator_out_data AS (
    id INTEGER,
    code TEXT,
    name TEXT,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE TYPE transport_user_train_leg_associated_service_out_data AS (
    service_id INTEGER,
    association_type INTEGER
);

CREATE TYPE transport_user_train_leg_service_call_out_data AS (
    station transport_user_train_leg_station_out_data,
    platform TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    associations transport_user_train_leg_associated_service_out_data[],
    mileage DECIMAL
);


CREATE TYPE transport_user_train_leg_service_out_data AS (
    service_id INTEGER,
    headcode TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    start_datetime TIMESTAMP WITH TIME ZONE,
    origins transport_user_train_leg_service_endpoint_out_data[],
    destinations transport_user_train_leg_service_endpoint_out_data[],
    operator transport_user_train_leg_operator_out_data,
    brand transport_user_train_leg_operator_out_data,
    power TEXT,
    calls transport_user_train_leg_call_out_data[]
);
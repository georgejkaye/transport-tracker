DROP TYPE train_leg_call_in_data CASCADE;
DROP TYPE train_leg_in_data CASCADE;

DROP TYPE train_leg_station_out_data CASCADE;
DROP TYPE train_leg_operator_out_data CASCADE;
DROP TYPE train_leg_associated_service_out_data CASCADE;
DROP TYPE train_leg_service_call_out_data CASCADE;
DROP TYPE train_leg_service_out_data CASCADE;
DROP TYPE train_leg_call_out_data CASCADE;
DROP TYPE train_leg_out_data CASCADE;

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

CREATE TYPE train_leg_station_out_data AS (
    crs TEXT,
    name TEXT
);

CREATE TYPE train_leg_operator_out_data AS (
    id INTEGER,
    code TEXT,
    name TEXT,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE TYPE train_leg_associated_service_out_data AS (
    service_id INTEGER,
    association_type INTEGER
);

CREATE TYPE train_leg_service_call_out_data AS (
    station train_leg_station_out_data,
    platform TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    associations train_leg_associated_service_out_data[],
    mileage DECIMAL
);

CREATE TYPE train_leg_service_out_data AS (
    service_id INTEGER,
    unique_identifier TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    headcode TEXT,
    start_datetime TIMESTAMP WITH TIME ZONE
    -- origins train_leg_service_endpoint_out_data[],
    -- destinations train_leg_service_endpoint_out_data[],
    -- operator train_leg_operator_out_data,
    -- brand train_leg_operator_out_data
);

CREATE TYPE train_leg_out_data AS (
    train_leg_id INTEGER,
    services train_leg_service_out_data[]
);

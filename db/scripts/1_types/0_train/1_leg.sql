DROP TYPE train_leg_call_in_data CASCADE;
DROP TYPE train_leg_in_data CASCADE;

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
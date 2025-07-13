CREATE TYPE train_station_out_data AS (
    station_id INTEGER,
    station_crs TEXT,
    station_name TEXT,
    operator_id INTEGER,
    brand_id INTEGER
);

CREATE TYPE train_brand_out_data AS (
    brand_id INTEGER,
    brand_code TEXT,
    brand_name TEXT,
    brand_bg TEXT,
    brand_fg TEXT
);

CREATE TYPE train_operator_out_data AS (
    operator_id INTEGER,
    operator_code TEXT,
    operator_name TEXT,
    operator_bg TEXT,
    operator_fg TEXT,
    operation_range DATERANGE,
    operator_brands train_brand_out_data[]
);

CREATE TYPE train_stock_subclass_out_data AS (
    stock_subclass INTEGER,
    stock_subclass_name TEXT,
    stock_cars INTEGER[]
);

CREATE TYPE train_stock_out_data AS (
    stock_class INTEGER,
    stock_class_name TEXT,
    stock_subclasses train_stock_subclass_out_data[]
);

CREATE TYPE train_service_in_data AS (
    unique_identifier TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    headcode TEXT,
    operator_id INTEGER,
    brand_id INTEGER,
    power TEXT
);

CREATE TYPE train_service_endpoint_in_data AS (
    unique_identifier TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    station_name TEXT,
    origin BOOLEAN
);

CREATE TYPE train_call_in_data AS (
    unique_identifier TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    station_crs TEXT,
    platform TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    mileage DECIMAL
);

CREATE TYPE train_associated_service_in_data AS (
    unique_identifier TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    station_crs TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    assoc_unique_identifier TEXT,
    assoc_run_date TIMESTAMP WITH TIME ZONE,
    assoc_type INTEGER
);

CREATE TYPE train_service_call_associated_service_in_data AS (
    associated_unique_identifier TEXT,
    associated_run_date TIMESTAMP WITH TIME ZONE,
    associated_type TEXT
);

CREATE TYPE train_service_call_in_data AS (
    station_crs TEXT,
    platform TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    mileage DECIMAL
);

CREATE TYPE train_service_in_data AS (
    unique_identifier TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    headcode TEXT,
    operator_code TEXT,
    brand_code TEXT,
    power TEXT
);

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
    mileage DECIMAL
);

CREATE TYPE train_stock_segment_in_data AS (
    stock_class INT,
    stock_subclass INT,
    stock_number INT,
    stock_cars INT,
    start_call_service_id TEXT,
    start_call_run_date TIMESTAMP WITH TIME ZONE,
    start_call_station_crs TEXT,
    start_call_plan_dep TIMESTAMP WITH TIME ZONE,
    start_call_act_dep TIMESTAMP WITH TIME ZONE,
    end_call_service_id TEXT,
    end_call_run_date TIMESTAMP WITH TIME ZONE,
    end_call_station_crs TEXT,
    end_call_plan_arr TIMESTAMP WITH TIME ZONE,
    end_call_act_arr TIMESTAMP WITH TIME ZONE
);

CREATE TYPE train_leg_in_data AS (
    user_id INT,
    leg_services train_service_in_data[],
    service_endpoints train_service_endpoint_in_data[],
    service_calls train_call_in_data[],
    service_associations train_associated_service_in_data[],
    leg_calls train_leg_call_in_data[],
    leg_distance DECIMAL,
    leg_stock train_stock_segment_in_data[]
);
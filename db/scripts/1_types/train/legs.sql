DROP TYPE IF EXISTS train_leg_call_in_data CASCADE;
DROP TYPE IF EXISTS train_leg_in_data CASCADE;

DROP TYPE IF EXISTS train_leg_station_out_data CASCADE;
DROP TYPE IF EXISTS train_leg_operator_out_data CASCADE;
DROP TYPE IF EXISTS train_leg_associated_service_out_data CASCADE;
DROP TYPE IF EXISTS train_leg_call_out_data CASCADE;
DROP TYPE IF EXISTS train_leg_service_out_data CASCADE;
DROP TYPE IF EXISTS train_leg_stock_report_out_data CASCADE;
DROP TYPE IF EXISTS train_leg_stock_segment_out_data CASCADE;
DROP TYPE IF EXISTS train_leg_out_data CASCADE;

DROP TYPE IF EXISTS train_leg_call_point_out_data CASCADE;
DROP TYPE IF EXISTS train_leg_call_points_out_data CASCADE;
DROP TYPE IF EXISTS train_leg_points_out_data CASCADE;

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
    mileage NUMERIC,
    associated_type_id INTEGER
);

CREATE TYPE train_leg_in_data AS (
    leg_services train_service_in_data[],
    service_endpoints train_service_endpoint_in_data[],
    service_calls train_call_in_data[],
    service_associations train_associated_service_in_data[],
    leg_calls train_leg_call_in_data[],
    leg_stock train_stock_segment_in_data[],
    leg_distance NUMERIC
);

CREATE TYPE train_leg_station_out_data AS (
    station_id INTEGER,
    station_crs TEXT,
    station_name TEXT
);

CREATE TYPE train_leg_operator_out_data AS (
    operator_id INTEGER,
    operator_code TEXT,
    operator_name TEXT
);

CREATE TYPE train_leg_associated_service_out_data AS (
    service_id INTEGER,
    association_type INTEGER
);

CREATE TYPE train_leg_call_out_data AS (
    station train_leg_station_out_data,
    platform TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    service_association_type TEXT,
    mileage NUMERIC
);

CREATE TYPE train_leg_service_out_data AS (
    service_id INTEGER,
    unique_identifier TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    headcode TEXT,
    start_datetime TIMESTAMP WITH TIME ZONE,
    origins train_leg_station_out_data[],
    destinations train_leg_station_out_data[],
    operator train_leg_operator_out_data,
    brand train_leg_operator_out_data
);

CREATE TYPE train_leg_stock_report_out_data AS (
    stock_class INTEGER,
    stock_subclass INTEGER,
    stock_number INTEGER,
    stock_cars INTEGER
);

CREATE TYPE train_leg_stock_segment_out_data AS (
    stock_start train_leg_station_out_data,
    stock_end train_leg_station_out_data,
    stock_reports train_leg_stock_report_out_data[]
);

CREATE TYPE train_leg_out_data AS (
    leg_id INTEGER,
    services train_leg_service_out_data[],
    calls train_leg_call_out_data[],
    stock train_leg_stock_segment_out_data[]
);

CREATE TYPE train_leg_call_point_out_data AS (
    platform TEXT,
    latitude NUMERIC,
    longitude NUMERIC
);

CREATE TYPE train_leg_call_points_out_data AS (
    station_id INTEGER,
    station_crs TEXT,
    station_name TEXT,
    platform TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    points train_leg_call_point_out_data[]
);

CREATE TYPE train_leg_points_out_data AS (
    leg_id INTEGER,
    operator_id INTEGER,
    brand_id INTEGER,
    call_points train_leg_call_points_out_data[]
);
DROP TYPE IF EXISTS train_leg_service_in_data CASCADE;
DROP TYPE IF EXISTS train_leg_service_endpoint_in_data CASCADE;
DROP TYPE IF EXISTS train_leg_service_call_in_data CASCADE;
DROP TYPE IF EXISTS train_leg_associated_service_in_data CASCADE;
DROP TYPE IF EXISTS train_leg_service_call_associated_service_in_data CASCADE;
DROP TYPE IF EXISTS train_leg_service_call_in_data CASCADE;
DROP TYPE IF EXISTS train_leg_call_in_data CASCADE;
DROP TYPE IF EXISTS train_leg_stock_segment_in_data CASCADE;
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

CREATE TYPE train_leg_service_in_data AS (
    unique_identifier TEXT_NOTNULL,
    run_date TIMESTAMP_NOTNULL,
    headcode TEXT_NOTNULL,
    operator_id INTEGER_NOTNULL,
    brand_id INTEGER,
    power TEXT
);

CREATE DOMAIN train_leg_service_in_data_notnull
AS train_leg_service_in_data NOT NULL;

CREATE TYPE train_leg_service_endpoint_in_data AS (
    unique_identifier TEXT_NOTNULL,
    run_date TIMESTAMP_NOTNULL,
    station_name TEXT_NOTNULL,
    origin BOOLEAN_NOTNULL
);

CREATE DOMAIN train_leg_service_endpoint_in_data_notnull
AS train_leg_service_endpoint_in_data NOT NULL;

CREATE TYPE train_leg_service_call_in_data AS (
    unique_identifier TEXT_NOTNULL,
    run_date TIMESTAMP_NOTNULL,
    station_crs TEXT_NOTNULL,
    platform TEXT_NOTNULL,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    mileage DECIMAL
);

CREATE DOMAIN train_leg_service_call_in_data_notnull
AS train_leg_service_call_in_data NOT NULL;

CREATE TYPE train_leg_associated_service_in_data AS (
    unique_identifier TEXT_NOTNULL,
    run_date TIMESTAMP_NOTNULL,
    station_crs TEXT_NOTNULL,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    assoc_unique_identifier TEXT_NOTNULL,
    assoc_run_date TIMESTAMP_NOTNULL,
    assoc_type INTEGER_NOTNULL
);

CREATE DOMAIN train_leg_associated_service_in_data_notnull
AS train_leg_associated_service_in_data NOT NULL;

CREATE TYPE train_leg_service_call_associated_service_in_data AS (
    associated_unique_identifier TEXT_NOTNULL,
    associated_run_date TIMESTAMP_NOTNULL,
    associated_type TEXT_NOTNULL
);

CREATE DOMAIN train_leg_service_call_associated_service_in_data_notnull
AS train_leg_service_call_associated_service_in_data NOT NULL;

CREATE TYPE train_leg_call_in_data AS (
    station_crs TEXT_NOTNULL,
    arr_call_service_uid TEXT_NOTNULL,
    arr_call_service_run_date TIMESTAMP_NOTNULL,
    arr_call_plan_arr TIMESTAMP WITH TIME ZONE,
    arr_call_act_arr TIMESTAMP WITH TIME ZONE,
    arr_call_plan_dep TIMESTAMP WITH TIME ZONE,
    arr_call_act_dep TIMESTAMP WITH TIME ZONE,
    dep_call_service_uid TEXT_NOTNULL,
    dep_call_service_run_date TIMESTAMP_NOTNULL,
    dep_call_plan_arr TIMESTAMP WITH TIME ZONE,
    dep_call_act_arr TIMESTAMP WITH TIME ZONE,
    dep_call_plan_dep TIMESTAMP WITH TIME ZONE,
    dep_call_act_dep TIMESTAMP WITH TIME ZONE,
    mileage DECIMAL,
    associated_type_id INTEGER
);

CREATE DOMAIN train_leg_call_in_data_notnull
AS train_leg_call_in_data NOT NULL;

CREATE TYPE train_leg_stock_segment_in_data AS (
    stock_class INT,
    stock_subclass INT,
    stock_number INT,
    stock_cars INT,
    start_call_service_uid TEXT_NOTNULL,
    start_call_service_run_date TIMESTAMP_NOTNULL,
    start_call_station_crs TEXT_NOTNULL,
    start_call_plan_dep TIMESTAMP_NOTNULL,
    start_call_act_dep TIMESTAMP_NOTNULL,
    end_call_service_uid TEXT_NOTNULL,
    end_call_service_run_date TIMESTAMP_NOTNULL,
    end_call_station_crs TEXT_NOTNULL,
    end_call_plan_arr TIMESTAMP_NOTNULL,
    end_call_act_arr TIMESTAMP_NOTNULL
);

CREATE DOMAIN train_leg_stock_segment_in_data_notnull
AS train_leg_stock_segment_in_data NOT NULL;

CREATE TYPE train_leg_in_data AS (
    leg_services train_leg_service_in_data_notnull[],
    service_endpoints train_leg_service_endpoint_in_data_notnull[],
    service_calls train_leg_service_call_in_data_notnull[],
    service_associations train_leg_associated_service_in_data_notnull[],
    leg_calls train_leg_call_in_data_notnull[],
    leg_stock train_leg_stock_segment_in_data_notnull[],
    leg_distance DECIMAL
);

CREATE DOMAIN train_leg_in_data_notnull
AS train_leg_in_data NOT NULL;

CREATE TYPE train_leg_station_out_data AS (
    station_id INTEGER_NOTNULL,
    station_crs TEXT_NOTNULL,
    station_name TEXT_NOTNULL
);

CREATE DOMAIN train_leg_station_out_data_notnull
AS train_leg_station_out_data NOT NULL;

CREATE TYPE train_leg_operator_out_data AS (
    operator_id INTEGER_NOTNULL,
    operator_code TEXT_NOTNULL,
    operator_name TEXT_NOTNULL
);

CREATE DOMAIN train_leg_operator_out_data_notnull
AS train_leg_operator_out_data NOT NULL;

CREATE TYPE train_leg_associated_service_out_data AS (
    service_id INTEGER_NOTNULL,
    association_type INTEGER_NOTNULL
);

CREATE DOMAIN train_leg_associated_service_out_data_notnull
AS train_leg_associated_service_out_data NOT NULL;

CREATE TYPE train_leg_call_out_data AS (
    station train_leg_station_out_data_notnull,
    platform TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    service_association_type TEXT,
    mileage DECIMAL
);

CREATE DOMAIN train_leg_call_out_data_notnull
AS train_leg_call_out_data NOT NULL;

CREATE TYPE train_leg_service_out_data AS (
    service_id INTEGER_NOTNULL,
    unique_identifier TEXT_NOTNULL,
    run_date TIMESTAMP_NOTNULL,
    headcode TEXT_NOTNULL,
    start_datetime TIMESTAMP_NOTNULL,
    origins train_leg_station_out_data_notnull[],
    destinations train_leg_station_out_data_notnull[],
    operator train_leg_operator_out_data_notnull,
    brand train_leg_operator_out_data
);

CREATE DOMAIN train_leg_service_out_data_notnull
AS train_leg_service_out_data NOT NULL;

CREATE TYPE train_leg_stock_report_out_data AS (
    stock_class INTEGER,
    stock_subclass INTEGER,
    stock_number INTEGER,
    stock_cars INTEGER
);

CREATE DOMAIN train_leg_stock_report_out_data_notnull
AS train_leg_stock_report_out_data NOT NULL;

CREATE TYPE train_leg_stock_segment_out_data AS (
    stock_start train_leg_station_out_data_notnull,
    stock_end train_leg_station_out_data_notnull,
    stock_reports train_leg_stock_report_out_data_notnull[]
);

CREATE DOMAIN train_leg_stock_segment_out_data_notnull
AS train_leg_stock_segment_out_data NOT NULL;

CREATE TYPE train_leg_out_data AS (
    leg_id INTEGER_NOTNULL,
    services train_leg_service_out_data_notnull[],
    calls train_leg_call_out_data_notnull[],
    stock train_leg_stock_segment_out_data_notnull[]
);

CREATE DOMAIN train_leg_out_data_notnull
AS train_leg_out_data NOT NULL;

CREATE TYPE train_leg_call_point_out_data AS (
    platform TEXT,
    latitude DECIMAL_NOTNULL,
    longitude DECIMAL_NOTNULL
);

CREATE DOMAIN train_leg_call_point_out_data_notnull
AS train_leg_call_point_out_data NOT NULL;

CREATE TYPE train_leg_call_points_out_data AS (
    station_id INTEGER_NOTNULL,
    station_crs TEXT_NOTNULL,
    station_name TEXT_NOTNULL,
    platform TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    points train_leg_call_point_out_data_notnull[]
);

CREATE DOMAIN train_leg_call_points_out_data_notnull
AS train_leg_call_points_out_data NOT NULL;

CREATE TYPE train_leg_points_out_data AS (
    leg_id INTEGER_NOTNULL,
    operator_id INTEGER_NOTNULL,
    brand_id INTEGER,
    call_points train_leg_call_points_out_data_notnull[]
);

CREATE DOMAIN train_leg_points_out_data_notnull
AS train_leg_points_out_data NOT NULL;
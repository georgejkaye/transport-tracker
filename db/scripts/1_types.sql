CREATE TYPE service_data AS (
    service_id TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    headcode CHARACTER(4),
    operator_code CHARACTER(2),
    brand_code CHARACTER(2),
    power TEXT
);

CREATE TYPE endpoint_data AS (
    service_id TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    station_crs CHARACTER(3),
    origin BOOLEAN
);

CREATE TYPE call_data AS (
    service_id TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    station_crs CHARACTER(3),
    platform TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    mileage DECIMAL
);

CREATE TYPE assoc_data AS (
    service_id TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    station_crs CHARACTER(3),
    plan_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    assoc_id TEXT,
    assoc_run_date TIMESTAMP WITH TIME ZONE,
    assoc_type TEXT
);

CREATE TYPE leg_data AS (
    distance DECIMAL
);

CREATE TYPE legcall_call_data AS (
    service_id TEXT,
    call_run_date TIMESTAMP WITH TIME ZONE,
    call_station_crs CHARACTER(3),
    call_plan_arr TIMESTAMP WITH TIME ZONE,
    call_plan_dep TIMESTAMP WITH TIME ZONE,
    call_act_arr TIMESTAMP WITH TIME ZONE,
    call_act_dep TIMESTAMP WITH TIME ZONE
);

CREATE TYPE legcall_data AS (
    arr_call_service_id TEXT,
    arr_call_run_date TIMESTAMP WITH TIME ZONE,
    arr_call_station_crs CHARACTER(3),
    arr_call_plan_arr TIMESTAMP WITH TIME ZONE,
    arr_call_plan_dep TIMESTAMP WITH TIME ZONE,
    arr_call_act_arr TIMESTAMP WITH TIME ZONE,
    arr_call_act_dep TIMESTAMP WITH TIME ZONE,
    dep_call_service_id TEXT,
    dep_call_run_date TIMESTAMP WITH TIME ZONE,
    dep_call_station_crs CHARACTER(3),
    dep_call_plan_arr TIMESTAMP WITH TIME ZONE,
    dep_call_plan_dep TIMESTAMP WITH TIME ZONE,
    dep_call_act_arr TIMESTAMP WITH TIME ZONE,
    dep_call_act_dep TIMESTAMP WITH TIME ZONE,
    mileage DECIMAL,
    assoc_type TEXT
);

CREATE TYPE stockreport_data AS (
    arr_call_service_id TEXT,
    arr_call_run_date TIMESTAMP WITH TIME ZONE,
    arr_call_station_crs CHARACTER(3),
    arr_call_plan_arr TIMESTAMP WITH TIME ZONE,
    arr_call_plan_dep TIMESTAMP WITH TIME ZONE,
    arr_call_act_arr TIMESTAMP WITH TIME ZONE,
    arr_call_act_dep TIMESTAMP WITH TIME ZONE,
    dep_call_service_id TEXT,
    dep_call_run_date TIMESTAMP WITH TIME ZONE,
    dep_call_station_crs CHARACTER(3),
    dep_call_plan_arr TIMESTAMP WITH TIME ZONE,
    dep_call_plan_dep TIMESTAMP WITH TIME ZONE,
    dep_call_act_arr TIMESTAMP WITH TIME ZONE,
    dep_call_act_dep TIMESTAMP WITH TIME ZONE,
    stock_class INT,
    stock_subclass INT,
    stock_number INT,
    stock_cars INT
);

CREATE TYPE OutOperatorData AS (
    operator_id INTEGER,
    operator_code TEXT,
    operator_name TEXT,
    operator_bg TEXT,
    operator_fg TEXT
);

CREATE TYPE OutBrandData AS (
    brand_id INTEGER,
    brand_code TEXT,
    brand_name TEXT,
    brand_bg TEXT,
    brand_fg TEXT
);

CREATE TYPE OutStationData AS (
    station_crs CHARACTER(3),
    station_name TEXT
);

CREATE TYPE OutAssocData AS (
    assoc_service_id TEXT,
    assoc_service_run_date TIMESTAMP WITH TIME ZONE,
    assoc_type TEXT
);

CREATE TYPE OutServiceAssocData AS (
    assoc_call_id INTEGER,
    assoc_service_id TEXT,
    assoc_service_run_date TIMESTAMP WITH TIME ZONE,
    assoc_type TEXT
);

CREATE TYPE OutCallData AS (
    station OutStationData,
    platform TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    assocs OutAssocData[],
    mileage DECIMAL
);

CREATE TYPE OutServiceData AS (
    service_id TEXT,
    service_run_date TIMESTAMP WITH TIME ZONE,
    service_headcode CHARACTER(4),
    service_start TIMESTAMP WITH TIME ZONE,
    service_origins OutStationData[],
    service_destinations OutStationData[],
    service_operator OutOperatorData,
    service_brand OutBrandData,
    service_calls OutCallData[],
    service_assocs OutServiceAssocData[]
);

CREATE TYPE OutStockData AS (
    stock_class INTEGER,
    stock_subclass INTEGER,
    stock_number INTEGER,
    stock_cars INTEGER
);

CREATE TYPE OutLegCallData AS (
    arr_call_id INTEGER,
    arr_service_id TEXT,
    arr_service_run_date TIMESTAMP WITH TIME ZONE,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    dep_call_id INTEGER,
    dep_service_id TEXT,
    dep_service_run_date TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    station OutStationData,
    platform TEXT,
    mileage DECIMAL,
    stocks OutStockData[],
    assocs OutAssocData[]
);

CREATE TYPE OutLegStock AS (
    segment_start TIMESTAMP WITH TIME ZONE,
    start_station OutStationData,
    end_station OutStationData,
    distance DECIMAL,
    duration INTERVAL,
    stock_data OutStockData[]
);

CREATE TYPE OutLegData AS (
    leg_id INTEGER,
    leg_start TIMESTAMP WITH TIME ZONE,
    leg_services OutServiceData[],
    leg_calls OutLegCallData[],
    leg_stocks OutLegStock[],
    leg_distance DECIMAL,
    leg_duration INTERVAL
);
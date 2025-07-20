DROP TYPE train_service_in_data CASCADE;
DROP TYPE train_service_endpoint_in_data CASCADE;
DROP TYPE train_call_in_data CASCADE;
DROP TYPE train_associated_service_in_data CASCADE;
DROP TYPE train_service_call_associated_service_in_data CASCADE;
DROP TYPE train_service_call_in_data CASCADE;

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
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
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

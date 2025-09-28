DROP TYPE IF EXISTS train_stock_subclass_out_data CASCADE;
DROP TYPE IF EXISTS train_stock_out_data CASCADE;
DROP TYPE IF EXISTS train_stock_segment_in_data CASCADE;

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

CREATE TYPE train_stock_segment_in_data AS (
    stock_class INT,
    stock_subclass INT,
    stock_number INT,
    stock_cars INT,
    start_call_service_uid TEXT,
    start_call_service_run_date TIMESTAMP WITH TIME ZONE,
    start_call_station_crs TEXT,
    start_call_plan_dep TIMESTAMP WITH TIME ZONE,
    start_call_act_dep TIMESTAMP WITH TIME ZONE,
    end_call_service_uid TEXT,
    end_call_service_run_date TIMESTAMP WITH TIME ZONE,
    end_call_station_crs TEXT,
    end_call_plan_arr TIMESTAMP WITH TIME ZONE,
    end_call_act_arr TIMESTAMP WITH TIME ZONE
);
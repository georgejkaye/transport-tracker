
-- out types

CREATE TYPE OutBrandData AS (
    brand_id INTEGER,
    brand_code TEXT,
    brand_name TEXT,
    brand_bg TEXT,
    brand_fg TEXT
);

CREATE TYPE TrainStationOutData AS (
    station_crs TEXT,
    station_name TEXT
);

CREATE TYPE TrainAssocData AS (
    assoc_service_id TEXT,
    assoc_service_run_date TIMESTAMP WITH TIME ZONE,
    assoc_type TEXT
);

CREATE TYPE TrainAssociatedServiceData AS (
    assoc_call_id INTEGER,
    assoc_service_id TEXT,
    assoc_service_run_date TIMESTAMP WITH TIME ZONE,
    assoc_type TEXT
);

CREATE TYPE TrainCallOutData AS (
    station TrainStationOutData,
    platform TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    assocs TrainAssocData[],
    mileage DECIMAL
);

CREATE TYPE TrainServiceOutData AS (
    service_id TEXT,
    service_run_date TIMESTAMP WITH TIME ZONE,
    service_headcode TEXT,
    service_start TIMESTAMP WITH TIME ZONE,
    service_origins TrainStationOutData[],
    service_destinations TrainStationOutData[],
    service_operator OutOperatorData,
    service_brand OutBrandData,
    service_calls TrainCallOutData[],
    service_assocs TrainAssociatedServiceData[]
);

CREATE TYPE TrainStockOutData AS (
    stock_class INTEGER,
    stock_subclass INTEGER,
    stock_number INTEGER,
    stock_cars INTEGER
);

CREATE TYPE TrainLegCallOutData AS (
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
    station TrainStationOutData,
    platform TEXT,
    mileage DECIMAL,
    stocks TrainStockOutData[],
    assocs TrainAssocData[]
);

CREATE TYPE TrainLegStockOutData AS (
    segment_start TIMESTAMP WITH TIME ZONE,
    start_station TrainStationOutData,
    end_station TrainStationOutData,
    distance DECIMAL,
    duration INTERVAL,
    stock_data TrainStockOutData[]
);

CREATE TYPE TrainLegOutData AS (
    leg_id INTEGER,
    user_id INTEGER,
    leg_start TIMESTAMP WITH TIME ZONE,
    leg_services TrainServiceOutData[],
    leg_calls TrainLegCallOutData[],
    leg_stocks TrainLegStockOutData[],
    leg_distance DECIMAL,
    leg_duration INTERVAL
);

CREATE TYPE LegStats AS (
    leg_id INTEGER,
    user_id INTEGER,
    board_time TIMESTAMP WITH TIME ZONE,
    board_crs TEXT,
    board_name TEXT,
    alight_time TIMESTAMP WITH TIME ZONE,
    alight_crs TEXT,
    alight_name TEXT,
    distance DECIMAL,
    duration INTERVAL,
    delay INTEGER,
    operator_id INTEGER,
    operator_code TEXT,
    operator_name TEXT,
    is_brand BOOLEAN
);

CREATE TYPE TrainStationStats AS (
    station_crs TEXT,
    station_name TEXT,
    operator_name TEXT,
    operator_id INTEGER,
    is_brand BOOLEAN,
    boards BIGINT,
    alights BIGINT,
    intermediates BIGINT
);

CREATE TYPE TrainOperatorStats AS (
    operator_id INTEGER,
    operator_name TEXT,
    is_brand BOOLEAN,
    count BIGINT,
    distance DECIMAL,
    duration INTERVAL,
    delay BIGINT
);

CREATE TYPE TrainUnitStats AS (
    stock_number INTEGER,
    count BIGINT,
    distance DECIMAL,
    duration INTERVAL
);

CREATE TYPE TrainClassStats AS (
    stock_class INTEGER,
    count BIGINT,
    distance DECIMAL,
    duration INTERVAL
);

CREATE TYPE TrainStats AS (
    journeys BIGINT,
    distance DECIMAL,
    duration INTERVAL,
    delay BIGINT,
    leg_stats LegStats[],
    station_stats StationStats[],
    operator_stats TrainOperatorStats[],
    class_stats TrainClassStats[],
    unit_stats TrainUnitStats[]
);

CREATE TYPE StationDetails AS (
    station_crs TEXT,
    station_name TEXT,
    latitude DECIMAL,
    longitude DECIMAL
);

CREATE TYPE StationLatLon AS (
    platform TEXT,
    latitude DECIMAL,
    longitude DECIMAL
);

CREATE TYPE StationCrsAndPlatform AS (
    station_crs TEXT,
    station_platform TEXT
);

CREATE TYPE StationNameAndPlatform AS (
    station_name TEXT,
    station_platform TEXT
);

CREATE TYPE StationAndPoints AS (
    station_crs TEXT,
    station_name TEXT,
    station_points StationLatLon[]
);

CREATE TYPE StationNameAndPoints AS (
    station_crs TEXT,
    station_name TEXT,
    search_name TEXT,
    station_points StationLatLon[]
);
CREATE TYPE BusStopInData AS (
    atco_code TEXT,
    naptan_code TEXT,
    stop_name TEXT,
    landmark_name TEXT,
    street_name TEXT,
    crossing_name TEXT,
    indicator TEXT,
    bearing TEXT,
    locality_name TEXT,
    parent_locality_name TEXT,
    grandparent_locality_name TEXT,
    town_name TEXT,
    suburb_name TEXT,
    latitude DECIMAL,
    longitude DECIMAL
);

CREATE TYPE BusStopOutData AS (
    bus_stop_id INT,
    atco_code TEXT,
    naptan_code TEXT,
    stop_name TEXT,
    landmark_name TEXT,
    street_name TEXT,
    crossing_name TEXT,
    indicator TEXT,
    bearing TEXT,
    locality_name TEXT,
    parent_locality_name TEXT,
    grandparent_locality_name TEXT,
    town_name TEXT,
    suburb_name TEXT,
    latitude DECIMAL,
    longitude DECIMAL
);

CREATE TYPE BusOperatorInData AS (
    bus_operator_name TEXT,
    bus_operator_national_code TEXT
);

CREATE TYPE BusOperatorOutData AS (
    bus_operator_id INT,
    bus_operator_name TEXT,
    bus_operator_national_code TEXT,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE TYPE BusServiceInData AS (
    service_line TEXT,
    bods_line_id TEXT,
    service_operator_national_code TEXT,
    service_outbound_description TEXT,
    service_inbound_description TEXT
);

CREATE TYPE BusServiceViaInData AS (
    bods_line_id TEXT,
    is_outbound BOOLEAN,
    via_name TEXT,
    via_index INT
);

CREATE TYPE BusServiceOutData AS (
    bus_service_id INT,
    bus_operator BusOperatorOutData,
    service_line TEXT,
    service_description_outbound TEXT,
    service_outbound_vias TEXT[],
    service_description_inbound TEXT,
    service_inbound_vias TEXT[],
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE TYPE BusServiceViaOutData AS (
    bus_service_id INT,
    is_outbound BOOLEAN,
    bus_service_vias TEXT[]
);

CREATE TYPE BusModelInData AS (
    model_name TEXT
);

CREATE TYPE BusVehicleInData AS (
    operator_id INT,
    operator_vehicle_id TEXT,
    bustimes_vehicle_id TEXT,
    vehicle_numberplate TEXT,
    vehicle_model TEXT,
    vehicle_livery_style TEXT,
    vehicle_name TEXT
);

CREATE TYPE BusVehicleOutData AS (
    bus_vehicle_id INT,
    bus_operator BusOperatorOutData,
    operator_vehicle_id TEXT,
    bustimes_vehicle_id TEXT,
    vehicle_numberplate TEXT,
    vehicle_model TEXT,
    vehicle_livery_style TEXT,
    vehicle_name TEXT
);

CREATE TYPE BusCallInData AS (
    call_index INT,
    stop_atco TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE
);

CREATE TYPE BusCallOutData AS (
    call_id INT,
    journey_id INT,
    call_index INT,
    bus_stop BusStopOutData,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE
);

CREATE TYPE BusJourneyInData AS (
    bustimes_id TEXT,
    service_id INT,
    journey_calls BusCallInData[],
    vehicle_id INT
);

CREATE TYPE BusJourneyOutData AS (
    journey_id INT,
    journey_service BusServiceOutData,
    journey_calls BusCallOutData[],
    journey_vehicle BusVehicleOutData
);

CREATE TYPE BusLegInData AS (
    journey BusJourneyInData,
    board_index INT,
    alight_index INT
);

CREATE TYPE BusOperatorOverviewOutData AS (
    operator_id INT,
    operator_name TEXT,
    operator_national_code TEXT
);

CREATE TYPE BusServiceOverviewOutData AS (
    service_id INT,
    service_line TEXT
);

CREATE TYPE BusLegOutData AS (
    leg_id INT,
    user_id UserOutPublicData,
    leg_journey BusJourneyOutData,
    leg_calls BusCallOutData[]
);

CREATE TYPE BusStopOverviewOutData AS (
    bus_stop_id BIGINT,
    stop_atco TEXT,
    stop_name TEXT,
    stop_locality TEXT,
    stop_street TEXT
);

CREATE TYPE BusCallOverviewOutData AS (
    bus_call_id INT,
    bus_stop BusStopOverviewOutData,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE
);

CREATE TYPE BusLegOverviewOutData AS (
    leg_id INT,
    bus_service BusServiceOverviewOutData,
    bus_operator BusOperatorOutData,
    leg_start BusCallOverviewOutData,
    leg_end BusCallOverviewOutData,
    leg_duration INTERVAL
);

CREATE TYPE BusVehicleOverviewOutData AS (
    vehicle_id INT,
    vehicle_operator_id TEXT,
    vehicle_name TEXT,
    vehicle_numberplate TEXT,
    vehicle_operator BusOperatorOutData,
    vehicle_legs BusLegOverviewOutData[],
    vehicle_duration INTERVAL
);
DROP TYPE BusStopInData CASCADE;
DROP TYPE BusOperatorInData CASCADE;
DROP TYPE BusServiceInData CASCADE;
DROP TYPE BusServiceViaInData CASCADE;
DROP TYPE BusModelInData CASCADE;
DROP TYPE BusVehicleInData CASCADE;
DROP TYPE BusCallInData CASCADE;
DROP TYPE BusJourneyInData CASCADE;
DROP TYPE BusLegInData CASCADE;

DROP TYPE BusStopDetails CASCADE;
DROP TYPE BusOperatorDetails CASCADE;
DROP TYPE BusServiceDetails CASCADE;
DROP TYPE BusVehicleDetails CASCADE;
DROP TYPE BusJourneyDetails CASCADE;
DROP TYPE BusJourneyServiceDetails CASCADE;
DROP TYPE BusCallDetails CASCADE;
DROP TYPE BusCallStopDetails CASCADE;
DROP TYPE BusJourneyCallDetails CASCADE;
DROP TYPE BusLegServiceDetails CASCADE;
DROP TYPE BusLegUserDetails CASCADE;
DROP TYPE BusVehicleLegDetails CASCADE;
DROP TYPE BusVehicleUserDetails CASCADE;
DROP TYPE BusStopLegDetails CASCADE;
DROP TYPE BusStopUserDetails CASCADE;

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

CREATE TYPE BusOperatorInData AS (
    operator_name TEXT,
    national_operator_code TEXT
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

CREATE TYPE BusModelInData AS (
    model_name TEXT
);

CREATE TYPE BusVehicleInData AS (
    operator_id INT,
    vehicle_identifier TEXT,
    bustimes_id TEXT,
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

CREATE TYPE BusJourneyInData AS (
    bustimes_id TEXT,
    service_id INT,
    journey_calls BusCallInData[],
    vehicle_id INT
);

CREATE TYPE BusLegInData AS (
    journey BusJourneyInData,
    board_index INT,
    alight_index INT
);

CREATE TYPE BusStopDetails AS (
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

CREATE TYPE BusOperatorDetails AS (
    bus_operator_id INT,
    operator_name TEXT,
    national_operator_code TEXT,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE TYPE BusServiceDetails AS (
    bus_service_id INT,
    bus_operator BusOperatorDetails,
    service_line TEXT,
    description_outbound TEXT,
    service_outbound_vias TEXT[],
    description_inbound TEXT,
    service_inbound_vias TEXT[],
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE TYPE BusVehicleDetails AS (
    bus_vehicle_id INT,
    bus_operator BusOperatorDetails,
    vehicle_identifier TEXT,
    bustimes_id TEXT,
    vehicle_numberplate TEXT,
    vehicle_model TEXT,
    vehicle_livery_style TEXT,
    vehicle_name TEXT
);

CREATE TYPE BusJourneyServiceDetails AS (
    service_id INT,
    service_operator BusOperatorDetails,
    service_line TEXT,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE TYPE BusCallStopDetails AS (
    bus_stop_id BIGINT,
    stop_atco TEXT,
    stop_name TEXT,
    stop_locality TEXT,
    stop_street TEXT,
    stop_indicator TEXT
);

CREATE TYPE BusJourneyCallDetails AS (
    call_id INT,
    call_index INT,
    bus_stop BusCallStopDetails,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE
);

CREATE TYPE BusJourneyDetails AS (
    journey_id INT,
    journey_service BusJourneyServiceDetails,
    journey_calls BusJourneyCallDetails[],
    journey_vehicle BusVehicleDetails
);

CREATE TYPE BusLegServiceDetails AS (
    service_id INT,
    service_line TEXT,
    bus_operator BusOperatorDetails,
    outbound_description TEXT,
    inbound_description TEXT,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE TYPE BusCallDetails AS (
    bus_call_id INT,
    call_index INT,
    bus_stop BusCallStopDetails,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE
);

CREATE TYPE BusLegUserDetails AS (
    leg_id INT,
    service BusLegServiceDetails,
    vehicle BusVehicleDetails,
    calls BusCallDetails[],
    duration INTERVAL
);

CREATE TYPE BusVehicleLegDetails AS (
    leg_id INT,
    bus_service BusLegServiceDetails,
    board_call BusCallDetails,
    alight_call BusCallDetails,
    duration INTERVAL
);

CREATE TYPE BusVehicleUserDetails AS (
    vehicle_id INT,
    identifier TEXT,
    name TEXT,
    numberplate TEXT,
    operator BusOperatorDetails,
    legs BusVehicleLegDetails[],
    duration INTERVAL
);

CREATE TYPE BusStopLegDetails AS (
    leg_id INT,
    bus_service BusLegServiceDetails,
    board_call BusCallDetails,
    alight_call BusCallDetails,
    this_call BusCallDetails,
    stops_before INT,
    stops_after INT
);

CREATE TYPE BusStopUserDetails AS (
    stop_id INT,
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
    longitude DECIMAL,
    stop_legs BusStopLegDetails[]
);
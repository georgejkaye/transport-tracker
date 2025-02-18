CREATE TYPE BusStopData AS (
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

CREATE TYPE BusOperatorOutData AS (
    bus_operator_id INT,
    bus_operator_name TEXT,
    bus_operator_code TEXT,
    bus_operator_national_code TEXT,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE TYPE BusServiceOutData AS (
    bus_service_id INT,
    bus_operator_id INT,
    service_line TEXT,
    service_description_outbound TEXT,
    service_description_inbound TEXT,
    bg_colour TEXT,
    fg_colour TEXT
);
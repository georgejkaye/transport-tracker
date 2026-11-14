CREATE TABLE bus_stop (
    bus_stop_id SERIAL PRIMARY KEY,
    atco_code TEXT UNIQUE NOT NULL,
    naptan_code TEXT NOT NULL,
    stop_name TEXT NOT NULL,
    landmark_name TEXT,
    street_name TEXT NOT NULL,
    crossing_name TEXT,
    indicator TEXT,
    bearing TEXT NOT NULL,
    locality_name TEXT NOT NULL,
    parent_locality_name TEXT,
    grandparent_locality_name TEXT,
    town_name TEXT,
    suburb_name TEXT,
    latitude DECIMAL,
    longitude DECIMAL
);

CREATE TABLE bus_operator (
    bus_operator_id SERIAL PRIMARY KEY,
    operator_name TEXT NOT NULL,
    national_operator_code TEXT UNIQUE NOT NULL,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE TABLE bus_service (
    bus_service_id SERIAL PRIMARY KEY,
    bods_line_id TEXT UNIQUE NOT NULL,
    bus_operator_id INT NOT NULL,
    service_line TEXT NOT NULL,
    description_outbound TEXT,
    description_inbound TEXT,
    bg_colour TEXT,
    fg_colour TEXT,
    FOREIGN KEY(bus_operator_id) REFERENCES bus_operator(bus_operator_id),
    UNIQUE (
        bus_service_id,
        description_outbound,
        description_inbound
    )
);

CREATE TABLE bus_service_via (
    bus_service_id INT NOT NULL,
    is_outbound BOOLEAN NOT NULL,
    via_name TEXT NOT NULL,
    via_index INT NOT NULL,
    FOREIGN KEY(bus_service_id) REFERENCES bus_service(bus_service_id),
    UNIQUE (bus_service_id, is_outbound, via_name, via_index)
);

CREATE TABLE bus_model (
    bus_model_id SERIAL PRIMARY KEY,
    bus_model_name TEXT UNIQUE NOT NULL
);

CREATE TABLE bus_vehicle (
    bus_vehicle_id SERIAL PRIMARY KEY,
    bus_operator_id INT NOT NULL,
    vehicle_identifier TEXT,
    bustimes_id TEXT,
    numberplate TEXT NOT NULL,
    bus_model_id INT,
    livery_style TEXT,
    vehicle_name TEXT,
    FOREIGN KEY(bus_operator_id) REFERENCES bus_operator(bus_operator_id),
    FOREIGN KEY(bus_model_id) REFERENCES bus_model(bus_model_id),
    UNIQUE (bus_operator_id, vehicle_identifier),
    UNIQUE (bus_operator_id, numberplate)
);

CREATE TABLE bus_journey (
    bus_journey_id SERIAL PRIMARY KEY,
    bus_service_id INT NOT NULL,
    bus_vehicle_id INT,
    FOREIGN KEY(bus_service_id) REFERENCES bus_service(bus_service_id),
    FOREIGN KEY(bus_vehicle_id) REFERENCES bus_vehicle(bus_vehicle_id)
);

CREATE TABLE bus_call (
    bus_call_id SERIAL PRIMARY KEY,
    bus_journey_id INT NOT NULL,
    call_index INT NOT NULL,
    bus_stop_id INT NOT NULL,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY(bus_journey_id) REFERENCES bus_journey(bus_journey_id),
    FOREIGN KEY(bus_stop_id) REFERENCES bus_stop(bus_stop_id)
);

CREATE TABLE bus_leg (
    bus_leg_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    bus_journey_id INT,
    board_call_index INT NOT NULL,
    alight_call_index INT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES Traveller(user_id),
    FOREIGN KEY(bus_journey_id) REFERENCES bus_journey(bus_journey_id),
);

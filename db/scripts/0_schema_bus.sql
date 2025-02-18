CREATE TABLE BusStop (
    bus_stop_id SERIAL PRIMARY KEY,
    atco_code TEXT NOT NULL,
    naptan_code TEXT NOT NULL,
    stop_name TEXT NOT NULL,
    landmark_name TEXT NOT NULL,
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

CREATE TABLE BusOperator (
    bus_operator_id SERIAL PRIMARY KEY,
    bus_operator_name TEXT NOT NULL,
    bus_operator_code TEXT NOT NULL,
    bus_operator_national_code TEXT NOT NULL,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE TABLE BusService (
    bus_service_id SERIAL PRIMARY KEY,
    bus_operator_id INT NOT NULL,
    service_line TEXT NOT NULL,
    service_description_outbound TEXT,
    service_description_inbound TEXT,
    bg_colour TEXT,
    fg_colour TEXT,
    FOREIGN KEY(bus_operator_id) REFERENCES BusOperator(bus_operator_id)
);

CREATE TABLE BusJourney (
    bus_journey_id SERIAL PRIMARY KEY,
    bus_service_id INT NOT NULL,
    FOREIGN KEY(bus_service_id) REFERENCES BusService(bus_service_id)
);

CREATE TABLE BusCall (
    bus_call_id SERIAL PRIMARY KEY,
    bus_journey_id INT NOT NULL,
    bus_stop_id INT NOT NULL,
    plan_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY(bus_journey_id) REFERENCES BusJourney(bus_journey_id),
    FOREIGN KEY(bus_stop_id) REFERENCES BusStop(bus_stop_id)
);

CREATE TABLE BusVehicle (
    bus_vehicle_id SERIAL PRIMARY KEY,
    vehicle_id TEXT,
    operator_id INT,
    FOREIGN KEY(operator_id) REFERENCES BusOperator(bus_operator_id)
);

CREATE TABLE BusLeg (
    bus_leg_id SERIAL PRIMARY KEY,
    bus_journey_id INT NOT NULL,
    bus_vehicle_id INT,
    FOREIGN KEY(bus_journey_id) REFERENCES BusJourney(bus_journey_id),
    FOREIGN KEY(bus_vehicle_id) REFERENCES BusVehicle(bus_vehicle_id)
);
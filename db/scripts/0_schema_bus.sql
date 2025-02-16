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
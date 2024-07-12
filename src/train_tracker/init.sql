CREATE TABLE Operator (
    operator_id CHARACTER(2) PRIMARY KEY,
    operator_name TEXT NOT NULL,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE TABLE Brand (
    brand_id CHARACTER(2) PRIMARY KEY,
    brand_name TEXT NOT NULL,
    parent_operator CHARACTER(2) NOT NULL,
    bg_colour TEXT,
    fg_colour TEXT,
    FOREIGN KEY (parent_operator) REFERENCES Operator(operator_id)
);

CREATE TABLE Stock (
    stock_class INT PRIMARY KEY,
    name TEXT
);

CREATE TABLE StockSubclass (
    stock_class INT NOT NULL,
    stock_subclass INT NOT NULL,
    name TEXT,
    PRIMARY KEY (stock_class, stock_subclass),
    FOREIGN KEY (stock_class) REFERENCES Stock(stock_class)
);

CREATE TABLE StockFormation (
    formation_id SERIAL PRIMARY KEY,
    stock_class INT NOT NULL,
    stock_subclass INT,
    cars INT,
    FOREIGN KEY (stock_class) REFERENCES Stock(stock_class),
    FOREIGN KEY (stock_class, stock_subclass) REFERENCES StockSubclass(stock_class, stock_subclass),
    CONSTRAINT stock_class_cars_unique UNIQUE NULLS NOT DISTINCT (stock_class, stock_subclass, cars)
);

CREATE TABLE OperatorStock (
    operator_id CHARACTER(2) NOT NULL,
    brand_id CHARACTER(2),
    stock_class INT NOT NULL,
    stock_subclass INT,
    FOREIGN KEY (operator_id) REFERENCES Operator(operator_id),
    FOREIGN KEY (brand_id) REFERENCES Brand(brand_id),
    FOREIGN KEY (stock_class) REFERENCES Stock(stock_class),
    FOREIGN KEY (stock_class, stock_subclass) REFERENCES StockSubclass(stock_class, stock_subclass),
    CONSTRAINT operator_stock_classes_unique UNIQUE NULLS NOT DISTINCT (operator_id, brand_id, stock_class, stock_subclass)
);

CREATE TABLE Station (
    station_crs CHARACTER(3) PRIMARY KEY,
    station_name TEXT NOT NULL,
    station_operator CHARACTER(2) NOT NULL,
    station_brand CHARACTER(2),
    FOREIGN KEY (station_operator) REFERENCES Operator(operator_id),
    FOREIGN KEY (station_brand) REFERENCES Brand(brand_id)
);

CREATE TABLE Leg (
    service_id TEXT NOT NULL,
    headcode TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    distance NUMERIC NOT NULL,
    board_crs CHARACTER(3) NOT NULL,
    alight_crs CHARACTER(3) NOT NULL,
    PRIMARY KEY (service_id, start_time),
    FOREIGN KEY (board_crs) REFERENCES Station(station_crs),
    FOREIGN KEY (alight_crs) REFERENCES Station(station_crs)
);

CREATE TABLE Call (
    service_id TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    station_crs CHARACTER(2) NOT NULL,
    plan_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (station_crs) REFERENCES Station(station_crs)
    FOREIGN KEY (service_id, start_time) REFERENCES Service(service_id, start_time)
);


CREATE TABLE ServiceOrigin (
    service_id TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    station_crs CHARACTER(3) NOT NULL,
    FOREIGN KEY (service_id, start_time) REFERENCES Service(service_id, start_time),
    FOREIGN KEY (station_crs) REFERENCES Station(station_crs)
);

CREATE TABLE ServiceDestination (
    service_id TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    station_crs CHARACTER(3) NOT NULL,
    FOREIGN KEY (service_id, start_time) REFERENCES Service(service_id, start_time),
    FOREIGN KEY (station_crs) REFERENCES Station(station_crs)
);

CREATE TABLE LegStock (
    service_id TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    stock_class INT,
    stock_subclass INT,
    stock_number INT,
    stock_cars INT,
    start_crs CHARACTER(3) NOT NULL,
    end_crs CHARACTER(3) NOT NULL,
    FOREIGN KEY (service_id, start_time) REFERENCES Leg(service_id, start_time),
    FOREIGN KEY (start_crs) REFERENCES Station(station_crs),
    FOREIGN KEY (end_crs) REFERENCES Station(station_crs)
);
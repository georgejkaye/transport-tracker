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
    stock_class INT NOT NULL,
    stock_subclass INT NOT NULL,
    cars INT NOT NULL,
    FOREIGN KEY (stock_class) REFERENCES Stock(stock_class),
    FOREIGN KEY (stock_class, stock_subclass) REFERENCES StockSubclass(stock_class, stock_subclass),
    CONSTRAINT stock_class_cars_unique UNIQUE (stock_class, stock_subclass, cars)
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

CREATE TABLE Service (
    service_id TEXT NOT NULL,
    run_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    headcode CHARACTER(4) NOT NULL,
    operator_id CHARACTER(2) NOT NULL,
    brand_id CHARACTER(2),
    power TEXT,
    PRIMARY KEY (service_id, run_date),
    FOREIGN KEY (operator_id) REFERENCES Operator(operator_id),
    FOREIGN KEY (brand_id) REFERENCES Brand(brand_id)
);

CREATE TABLE ServiceEndpoint (
    service_id TEXT NOT NULL,
    run_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    station_crs CHARACTER(3) NOT NULL,
    origin BOOLEAN NOT NULL,
    CONSTRAINT endpoint_unique UNIQUE (service_id, run_date, station_crs, origin),
    FOREIGN KEY (service_id, run_date) REFERENCES Service(service_id, run_date) ON DELETE CASCADE,
    FOREIGN KEY (station_crs) REFERENCES Station(station_crs)
);

CREATE TABLE Call (
    call_id SERIAL PRIMARY KEY,
    service_id TEXT NOT NULL,
    run_date TIMESTAMP WITH TIME ZONE NOT NULL,
    station_crs CHARACTER(3) NOT NULL,
    platform TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    mileage NUMERIC,
    CONSTRAINT call_arr_unique UNIQUE (service_id, run_date, station_crs, plan_arr),
    CONSTRAINT call_dep_unique UNIQUE (service_id, run_date, station_crs, plan_dep),
    FOREIGN KEY (service_id, run_date) REFERENCES Service(service_id, run_date) ON DELETE CASCADE,
    FOREIGN KEY (station_crs) REFERENCES Station(station_crs),
    CONSTRAINT mileage_positive CHECK (mileage >= 0)
);

CREATE TABLE AssociatedType (
    associated_type TEXT PRIMARY KEY
);

INSERT INTO AssociatedType(associated_type) VALUES ('DIVIDES_TO');
INSERT INTO AssociatedType(associated_type) VALUES ('DIVIDES_FROM');
INSERT INTO AssociatedType(associated_type) VALUES ('JOINS_TO');
INSERT INTO AssociatedType(associated_type) VALUES ('JOINS_WITH');

CREATE TABLE AssociatedService (
    call_id INT NOT NULL,
    associated_id TEXT NOT NULL,
    associated_run_date TIMESTAMP WITH TIME ZONE NOT NULL,
    associated_type TEXT NOT NULL,
    FOREIGN KEY (associated_type) REFERENCES AssociatedType(associated_type),
    FOREIGN KEY (call_id) REFERENCES Call(call_id) ON DELETE CASCADE,
    FOREIGN KEY (associated_id, associated_run_date) REFERENCES Service(service_id, run_date) ON DELETE CASCADE,
    CONSTRAINT assoc_unique UNIQUE (call_id, associated_id, associated_run_date, associated_type)
);

CREATE TABLE Leg (
    leg_id SERIAL PRIMARY KEY,
    distance NUMERIC NOT NULL,
    CONSTRAINT distance_positive CHECK (distance > 0)
);

CREATE TABLE LegCall (
    leg_id INT NOT NULL,
    arr_call_id INT,
    dep_call_id INT,
    mileage NUMERIC,
    assoc_type TEXT,
    CONSTRAINT leg_call_unique UNIQUE (leg_id, arr_call_id, dep_call_id),
    FOREIGN KEY (leg_id) REFERENCES Leg(leg_id) ON DELETE CASCADE,
    FOREIGN KEY (arr_call_id) REFERENCES Call(call_id) ON DELETE CASCADE,
    FOREIGN KEY (dep_call_id) REFERENCES Call(call_id) ON DELETE CASCADE,
    FOREIGN KEY (assoc_type) REFERENCES AssociatedType(associated_type),
    CONSTRAINT mileage_positive CHECK (mileage >= 0),
    CONSTRAINT arr_or_dep CHECK (num_nulls(arr_call_id, dep_call_id) <= 1)
);

CREATE OR REPLACE FUNCTION validStockFormation (
    stockclass INT,
    stocksubclass INT,
    stockcars INT
) RETURNS BOOLEAN
LANGUAGE plpgsql
AS
$$
BEGIN
    IF stockclass IS NULL
    THEN
        RETURN TRUE;
    END IF;
    IF stocksubclass IS NULL
    THEN
        IF stockcars IS NULL
        THEN
            RETURN EXISTS(
                SELECT * FROM StockFormation
                WHERE stock_class = stockclass
            );
        ELSE
            RETURN EXISTS(
                SELECT * FROM StockFormation
                WHERE stock_class = stockclass AND cars = stockcars
            );
        END IF;
    END IF;
    RETURN EXISTS (
        SELECT * FROM StockFormation
        WHERE stock_class = stockclass AND stock_subclass = stocksubclass AND cars = stockcars
    );
END;
$$;

CREATE TABLE StockSegment (
    stock_class INT,
    stock_subclass INT,
    stock_number INT,
    stock_cars INT,
    start_call INT NOT NULL,
    end_call INT NOT NULL,
    distance NUMERIC,
    FOREIGN KEY (stock_class) REFERENCES Stock(stock_class),
    FOREIGN KEY (stock_class, stock_subclass) REFERENCES StockSubclass(stock_class, stock_subclass),
    FOREIGN KEY (start_call) REFERENCES Call(call_id) ON DELETE CASCADE,
    FOREIGN KEY (end_call) REFERENCES Call(call_id) ON DELETE CASCADE,
    CONSTRAINT valid_stock CHECK (validStockFormation(stock_class, stock_subclass, stock_cars)),
    CONSTRAINT distance_positive CHECK (distance > 0)
);
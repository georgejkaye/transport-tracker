CREATE EXTENSION btree_gist;

CREATE TABLE OperatorCode (
    operator_code CHARACTER(2) PRIMARY KEY
);

CREATE TABLE Operator (
    operator_id SERIAL PRIMARY KEY,
    operator_code CHARACTER(2),
    operator_name TEXT NOT NULL,
    bg_colour TEXT,
    fg_colour TEXT,
    operation_range DATERANGE NOT NULL,
    FOREIGN KEY (operator_code) REFERENCES OperatorCode(operator_code),
    CONSTRAINT no_overlapping_operators
    exclude USING gist (
        operator_id WITH =, operation_range WITH &&
    )
);

CREATE TABLE Brand (
    brand_id SERIAL PRIMARY KEY,
    brand_code CHARACTER(2),
    brand_name TEXT NOT NULL,
    parent_operator INTEGER NOT NULL,
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
    stock_subclass INT,
    cars INT NOT NULL,
    FOREIGN KEY (stock_class) REFERENCES Stock(stock_class),
    FOREIGN KEY (stock_class, stock_subclass) REFERENCES StockSubclass(stock_class, stock_subclass),
    CONSTRAINT stock_class_cars_unique UNIQUE (stock_class, stock_subclass, cars)
);

CREATE OR REPLACE FUNCTION IsValidBrand(
    p_brand_id INT,
    p_operator_id INT
) RETURNS BOOLEAN
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN p_brand_id IS NULL
        OR (p_brand_id IS NULL AND p_operator_id IS NULL)
        OR (SELECT parent_operator FROM public.brand WHERE brand_id = p_brand_id) = p_operator_id;
END;
$$;

CREATE TABLE OperatorStock (
    operator_id INTEGER NOT NULL,
    brand_id INTEGER,
    stock_class INT NOT NULL,
    stock_subclass INT,
    FOREIGN KEY (operator_id) REFERENCES Operator(operator_id),
    FOREIGN KEY (brand_id) REFERENCES Brand(brand_id),
    FOREIGN KEY (stock_class) REFERENCES Stock(stock_class),
    FOREIGN KEY (stock_class, stock_subclass) REFERENCES StockSubclass(stock_class, stock_subclass),
    CONSTRAINT operator_stock_classes_unique UNIQUE NULLS NOT DISTINCT (operator_id, brand_id, stock_class, stock_subclass),
    CONSTRAINT valid_brand CHECK (IsValidBrand(brand_id, operator_id))
);

CREATE TABLE Station (
    station_crs CHARACTER(3) PRIMARY KEY,
    station_name TEXT NOT NULL,
    operator_id INTEGER NOT NULL,
    brand_id INTEGER,
    station_img TEXT,
    FOREIGN KEY (operator_id) REFERENCES Operator(operator_id),
    FOREIGN KEY (brand_id) REFERENCES Brand(brand_id),
    CONSTRAINT valid_brand CHECK (IsValidBrand(brand_id, operator_id))
);

CREATE TABLE StationName (
    station_crs CHARACTER(3) NOT NULL,
    alternate_station_name TEXT NOT NULL,
    FOREIGN KEY (station_crs) REFERENCES Station(station_crs)
);

CREATE TABLE StationPoint (
    station_crs CHARACTER(3),
    platform TEXT,
    latitude DECIMAL NOT NULL,
    longitude DECIMAL NOT NULL,
    FOREIGN KEY (station_crs) REFERENCES Station(station_crs),
    CONSTRAINT point_unique UNIQUE NULLS NOT DISTINCT (station_crs, platform)
);

CREATE TABLE Service (
    service_id TEXT NOT NULL,
    run_date TIMESTAMP WITH TIME ZONE NOT NULL,
    headcode CHARACTER(4) NOT NULL,
    operator_id INTEGER NOT NULL,
    brand_id INTEGER,
    power TEXT,
    PRIMARY KEY (service_id, run_date),
    FOREIGN KEY (operator_id) REFERENCES Operator(operator_id),
    FOREIGN KEY (brand_id) REFERENCES Brand(brand_id),
    CONSTRAINT valid_brand CHECK (IsValidBrand(brand_id, operator_id))
);

CREATE TABLE ServiceEndpoint (
    service_id TEXT NOT NULL,
    run_date TIMESTAMP WITH TIME ZONE NOT NULL,
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
    leg_call_id SERIAL PRIMARY KEY,
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

CREATE TABLE StockSegment (
    stock_segment_id SERIAL PRIMARY KEY,
    start_call INT NOT NULL,
    end_call INT NOT NULL,
    FOREIGN KEY (start_call) REFERENCES Call(call_id) ON DELETE CASCADE,
    FOREIGN KEY (end_call) REFERENCES Call(call_id) ON DELETE CASCADE,
    CONSTRAINT stock_segment_unique UNIQUE (start_call, end_call)
);

CREATE OR REPLACE FUNCTION IsValidStockFormation (
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
                SELECT * FROM public.StockFormation
                WHERE stock_class = stockclass
            );
        ELSE
            RETURN EXISTS(
                SELECT * FROM public.StockFormation
                WHERE stock_class = stockclass AND cars = stockcars
            );
        END IF;
    END IF;
    RETURN EXISTS (
        SELECT * FROM public.StockFormation
        WHERE stock_class = stockclass AND stock_subclass = stocksubclass AND cars = stockcars
    );
END;
$$;

CREATE TABLE StockReport (
    stock_report_id SERIAL PRIMARY KEY,
    stock_class INT,
    stock_subclass INT,
    stock_number INT,
    stock_cars INT,
    FOREIGN KEY (stock_class) REFERENCES Stock(stock_class),
    FOREIGN KEY (stock_class, stock_subclass) REFERENCES StockSubclass(stock_class, stock_subclass),
    CONSTRAINT valid_stock CHECK (IsValidStockFormation(stock_class, stock_subclass, stock_cars))
);

CREATE TABLE StockSegmentReport (
    stock_segment_id INT NOT NULL,
    stock_report_id INT NOT NULL,
    FOREIGN KEY (stock_segment_id) REFERENCES StockSegment(stock_segment_id),
    FOREIGN KEY (stock_report_id) REFERENCES StockReport(stock_report_id)
);

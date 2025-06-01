CREATE EXTENSION btree_gist;

CREATE TABLE TrainOperatorCode (
    operator_code TEXT PRIMARY KEY
);

CREATE TABLE TrainOperator (
    operator_id SERIAL PRIMARY KEY,
    operator_code TEXT,
    operator_name TEXT NOT NULL,
    bg_colour TEXT,
    fg_colour TEXT,
    operation_range DATERANGE NOT NULL,
    FOREIGN KEY (operator_code) REFERENCES TrainOperatorCode(operator_code),
    CONSTRAINT no_overlapping_operators
    exclude USING gist (
        operator_id WITH =, operation_range WITH &&
    )
);

CREATE TABLE TrainBrand (
    brand_id SERIAL PRIMARY KEY,
    brand_code TEXT,
    brand_name TEXT NOT NULL,
    parent_operator INTEGER NOT NULL,
    bg_colour TEXT,
    fg_colour TEXT,
    FOREIGN KEY (parent_operator) REFERENCES TrainOperator(operator_id)
);

CREATE TABLE TrainStock (
    stock_class INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE TrainStockSubclass (
    stock_class INTEGER NOT NULL,
    stock_subclass INTEGER NOT NULL,
    name TEXT,
    PRIMARY KEY (stock_class, stock_subclass),
    FOREIGN KEY (stock_class) REFERENCES TrainStock(stock_class)
);

CREATE TABLE TrainStockFormation (
    stock_class INTEGER NOT NULL,
    stock_subclass INTEGER,
    cars INTEGER NOT NULL,
    FOREIGN KEY (stock_class) REFERENCES TrainStock(stock_class),
    FOREIGN KEY (stock_class, stock_subclass) REFERENCES TrainStockSubclass(stock_class, stock_subclass),
    CONSTRAINT stock_class_cars_unique UNIQUE (stock_class, stock_subclass, cars)
);

CREATE OR REPLACE FUNCTION IsValidBrand(
    p_brand_id INTEGER,
    p_operator_id INT
) RETURNS BOOLEAN
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN p_brand_id IS NULL
        OR (p_brand_id IS NULL AND p_operator_id IS NULL)
        OR (SELECT parent_operator FROM TrainBrand WHERE brand_id = p_brand_id) = p_operator_id;
END;
$$;

CREATE TABLE TrainOperatorStock (
    operator_id INTEGER NOT NULL,
    brand_id INTEGER,
    stock_class INTEGER NOT NULL,
    stock_subclass INTEGER,
    FOREIGN KEY (operator_id) REFERENCES TrainOperator(operator_id),
    FOREIGN KEY (brand_id) REFERENCES TrainBrand(brand_id),
    FOREIGN KEY (stock_class) REFERENCES TrainStock(stock_class),
    FOREIGN KEY (stock_class, stock_subclass) REFERENCES TrainStockSubclass(stock_class, stock_subclass),
    CONSTRAINT operator_stock_classes_unique UNIQUE NULLS NOT DISTINCT (operator_id, brand_id, stock_class, stock_subclass),
    CONSTRAINT valid_brand CHECK (IsValidBrand(brand_id, operator_id))
);

CREATE TABLE TrainStation (
    station_id SERIAL PRIMARY KEY,
    station_crs TEXT NOT NULL,
    station_name TEXT NOT NULL,
    operator_id INTEGER NOT NULL,
    brand_id INTEGER,
    station_img TEXT,
    FOREIGN KEY (operator_id) REFERENCES TrainOperator(operator_id),
    FOREIGN KEY (brand_id) REFERENCES TrainBrand(brand_id),
    CONSTRAINT valid_brand CHECK (IsValidBrand(brand_id, operator_id)),
    CONSTRAINT trainstation_check_station_crs_length CHECK (VALUE ~ '^[[:alpha:]]{3}$'),
    CONSTRAINT trainstation_station_crs_unique UNIQUE station_crs
);

CREATE TABLE TrainStationName (
    station_id INT NOT NULL,
    alternate_station_name TEXT NOT NULL,
    FOREIGN KEY (station_id) REFERENCES TrainStation(station_id)
);

CREATE TABLE TrainStationPoint (
    station_id INT NOT NULL,
    platform TEXT,
    latitude DECIMAL NOT NULL,
    longitude DECIMAL NOT NULL,
    FOREIGN KEY (station_id) REFERENCES TrainStation(station_id),
    CONSTRAINT point_unique UNIQUE NULLS NOT DISTINCT (station_id, platform)
);

CREATE TABLE TrainService (
    service_id SERIAL PRIMARY KEY,
    unique_identifier TEXT NOT NULL,
    run_date TIMESTAMP WITH TIME ZONE NOT NULL,
    headcode TEXT NOT NULL,
    operator_id INTEGER NOT NULL,
    brand_id INTEGER,
    power TEXT,
    FOREIGN KEY (operator_id) REFERENCES TrainOperator(operator_id),
    FOREIGN KEY (brand_id) REFERENCES TrainBrand(brand_id),
    CONSTRAINT trainservice_service_id_run_date_unique UNIQUE (service_id, run_date),
    CONSTRAINT trainservice_check_is_valid_brand CHECK (IsValidBrand(brand_id, operator_id))
    CONSTRAINT trainservice_check_headcode_length CHECK (LENGTH(headcode) = 4)
);

CREATE TABLE TrainServiceEndpoint (
    service_id INT NOT NULL,
    station_id INT NOT NULL,
    origin BOOLEAN NOT NULL,
    CONSTRAINT trainserviceendpoint_service_id_station_crs_origin_unique UNIQUE (service_id, station_id, origin),
    FOREIGN KEY (service_id) REFERENCES TrainService(service_id) ON DELETE CASCADE,
    FOREIGN KEY (station_id) REFERENCES TrainStation(station_crs)
);

CREATE TABLE TrainCall (
    call_id SERIAL PRIMARY KEY,
    service_id INT NOT NULL,
    station_id INT NOT NULL,
    platform TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    mileage NUMERIC,
    CONSTRAINT call_arr_unique UNIQUE (service_id, run_date, station_crs, plan_arr),
    CONSTRAINT call_dep_unique UNIQUE (service_id, run_date, station_crs, plan_dep),
    FOREIGN KEY (service_id) REFERENCES TrainService(service_id) ON DELETE CASCADE,
    FOREIGN KEY (station_id) REFERENCES TrainStation(station_id),
    CONSTRAINT mileage_positive CHECK (mileage >= 0)
);

CREATE TABLE TrainAssociatedServiceType (
    associated_type TEXT PRIMARY KEY
);

INSERT INTO TrainAssociatedServiceType(associated_type) VALUES ('DIVIDES_TO');
INSERT INTO TrainAssociatedServiceType(associated_type) VALUES ('DIVIDES_FROM');
INSERT INTO TrainAssociatedServiceType(associated_type) VALUES ('JOINS_TO');
INSERT INTO TrainAssociatedServiceType(associated_type) VALUES ('JOINS_WITH');

CREATE TABLE TrainAssociatedService (
    call_id INTEGER NOT NULL,
    associated_service_id INT NOT NULL,
    associated_type TEXT NOT NULL,
    FOREIGN KEY (associated_type) REFERENCES TrainAssociatedServiceType(associated_type),
    FOREIGN KEY (call_id) REFERENCES TrainCall(call_id) ON DELETE CASCADE,
    FOREIGN KEY (associated_service_id) REFERENCES TrainService(service_id) ON DELETE CASCADE,
    CONSTRAINT assoc_unique UNIQUE (call_id, associated_service_id, associated_type)
);

CREATE TABLE TrainLeg (
    leg_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    distance NUMERIC NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Traveller(user_id),
    CONSTRAINT distance_positive CHECK (distance > 0)
);

CREATE TABLE TrainLegCall (
    leg_call_id SERIAL PRIMARY KEY,
    leg_id INTEGER NOT NULL,
    arr_call_id INTEGER,
    dep_call_id INTEGER,
    mileage NUMERIC,
    assoc_type TEXT,
    CONSTRAINT leg_call_unique UNIQUE (leg_id, arr_call_id, dep_call_id),
    FOREIGN KEY (leg_id) REFERENCES TrainLeg(leg_id) ON DELETE CASCADE,
    FOREIGN KEY (arr_call_id) REFERENCES TrainCall(call_id) ON DELETE CASCADE,
    FOREIGN KEY (dep_call_id) REFERENCES TrainCall(call_id) ON DELETE CASCADE,
    FOREIGN KEY (assoc_type) REFERENCES TrainAssociatedServiceType(associated_type),
    CONSTRAINT mileage_positive CHECK (mileage >= 0),
    CONSTRAINT arr_or_dep CHECK (num_nulls(arr_call_id, dep_call_id) <= 1)
);

CREATE TABLE TrainStockSegment (
    stock_segment_id SERIAL PRIMARY KEY,
    start_call INTEGER NOT NULL,
    end_call INTEGER NOT NULL,
    FOREIGN KEY (start_call) REFERENCES TrainCall(call_id) ON DELETE CASCADE,
    FOREIGN KEY (end_call) REFERENCES TrainCall(call_id) ON DELETE CASCADE,
    CONSTRAINT stock_segment_unique UNIQUE (start_call, end_call)
);

CREATE OR REPLACE FUNCTION IsValidStockFormation (
    stockclass INTEGER,
    stocksubclass INTEGER,
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
                SELECT * FROM public.TrainStockFormation
                WHERE stock_class = stockclass
            );
        ELSE
            RETURN EXISTS(
                SELECT * FROM public.TrainStockFormation
                WHERE stock_class = stockclass AND cars = stockcars
            );
        END IF;
    END IF;
    RETURN EXISTS (
        SELECT * FROM public.TrainStockFormation
        WHERE stock_class = stockclass AND stock_subclass = stocksubclass AND cars = stockcars
    );
END;
$$;

CREATE TABLE TrainStockReport (
    stock_report_id SERIAL PRIMARY KEY,
    stock_class INTEGER,
    stock_subclass INTEGER,
    stock_number INTEGER,
    stock_cars INTEGER,
    FOREIGN KEY (stock_class) REFERENCES TrainStock(stock_class),
    FOREIGN KEY (stock_class, stock_subclass) REFERENCES TrainStockSubclass(stock_class, stock_subclass),
    CONSTRAINT valid_stock CHECK (IsValidStockFormation(stock_class, stock_subclass, stock_cars))
);

CREATE TABLE TrainStockSegmentReport (
    stock_segment_id INTEGER NOT NULL,
    stock_report_id INTEGER NOT NULL,
    FOREIGN KEY (stock_segment_id) REFERENCES TrainStockSegment(stock_segment_id),
    FOREIGN KEY (stock_report_id) REFERENCES TrainStockReport(stock_report_id)
);

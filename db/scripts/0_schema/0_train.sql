CREATE EXTENSION btree_gist;

CREATE TABLE train_operator_code (
    operator_code TEXT PRIMARY KEY
);

CREATE TABLE train_operator (
    operator_id SERIAL PRIMARY KEY,
    operator_code TEXT,
    operator_name TEXT NOT NULL,
    bg_colour TEXT,
    fg_colour TEXT,
    operation_range DATERANGE NOT NULL,
    FOREIGN KEY (operator_code) REFERENCES train_operator_code(operator_code),
    CONSTRAINT no_overlapping_operators
    exclude USING gist (
        operator_id WITH =, operation_range WITH &&
    )
);

CREATE TABLE train_brand (
    brand_id SERIAL PRIMARY KEY,
    brand_code TEXT,
    brand_name TEXT NOT NULL,
    parent_operator INTEGER NOT NULL,
    bg_colour TEXT,
    fg_colour TEXT,
    FOREIGN KEY (parent_operator) REFERENCES train_operator(operator_id)
);

CREATE TABLE train_stock (
    stock_class INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE train_stock_subclass (
    stock_class INTEGER NOT NULL,
    stock_subclass INTEGER NOT NULL,
    name TEXT,
    PRIMARY KEY (stock_class, stock_subclass),
    FOREIGN KEY (stock_class) REFERENCES train_stock(stock_class)
);

CREATE TABLE train_stock_formation (
    stock_class INTEGER NOT NULL,
    stock_subclass INTEGER,
    cars INTEGER NOT NULL,
    FOREIGN KEY (stock_class) REFERENCES train_stock(stock_class),
    FOREIGN KEY (stock_class, stock_subclass) REFERENCES train_stock_subclass(stock_class, stock_subclass),
    CONSTRAINT stock_class_cars_unique UNIQUE (stock_class, stock_subclass, cars)
);

CREATE OR REPLACE FUNCTION is_valid_brand(
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

CREATE TABLE train_operator_stock (
    operator_id INTEGER NOT NULL,
    brand_id INTEGER,
    stock_class INTEGER NOT NULL,
    stock_subclass INTEGER,
    FOREIGN KEY (operator_id) REFERENCES train_operator(operator_id),
    FOREIGN KEY (brand_id) REFERENCES train_brand(brand_id),
    FOREIGN KEY (stock_class) REFERENCES train_stock(stock_class),
    FOREIGN KEY (stock_class, stock_subclass)
        REFERENCES train_stock_subclass(stock_class, stock_subclass),
    CONSTRAINT train_operator_stock_unique_stock
        UNIQUE
            NULLS NOT DISTINCT
            (operator_id, brand_id, stock_class, stock_subclass),
    CONSTRAINT valid_brand CHECK (is_valid_brand(brand_id, operator_id))
);

CREATE TABLE train_station (
    train_station_id SERIAL PRIMARY KEY,
    station_crs TEXT NOT NULL,
    station_name TEXT NOT NULL,
    operator_id INTEGER NOT NULL,
    brand_id INTEGER,
    station_img TEXT,
    FOREIGN KEY (operator_id) REFERENCES train_operator(operator_id),
    FOREIGN KEY (brand_id) REFERENCES train_brand(brand_id),
    CONSTRAINT valid_brand CHECK (is_valid_brand(brand_id, operator_id)),
    CONSTRAINT train_station_check_station_crs_length
        CHECK (VALUE ~ '^[[:alpha:]]{3}$'),
    CONSTRAINT train_station_unique_station_crs UNIQUE station_crs
);

CREATE TABLE train_station_name (
    train_station_id INT NOT NULL,
    alternate_station_name TEXT NOT NULL,
    FOREIGN KEY (train_station_id) REFERENCES train_station(station_id)
);

CREATE TABLE train_station_point (
    train_station_id INT NOT NULL,
    platform TEXT,
    latitude DECIMAL NOT NULL,
    longitude DECIMAL NOT NULL,
    FOREIGN KEY (train_station_id) REFERENCES train_station(station_id),
    CONSTRAINT point_unique
        UNIQUE NULLS NOT DISTINCT (train_station_id, platform)
);

CREATE TABLE train_service (
    train_service_id SERIAL PRIMARY KEY,
    unique_identifier TEXT NOT NULL,
    run_date TIMESTAMP WITH TIME ZONE NOT NULL,
    headcode TEXT NOT NULL,
    operator_id INTEGER NOT NULL,
    brand_id INTEGER,
    power TEXT,
    FOREIGN KEY (operator_id) REFERENCES train_operator(operator_id),
    FOREIGN KEY (brand_id) REFERENCES TrainBrand(brand_id),
    CONSTRAINT train_service_unique_service_id_run_date
        UNIQUE (train_service_id, run_date),
    CONSTRAINT train_service_check_is_valid_brand
        CHECK (is_valid_brand(brand_id, operator_id))
    CONSTRAINT train_service_check_headcode_length
        CHECK (LENGTH(headcode) = 4)
);

CREATE TABLE train_service_endpoint (
    train_service_id INT NOT NULL,
    train_station_id INT NOT NULL,
    origin BOOLEAN NOT NULL,
    CONSTRAINT train_service_endpoint_service_id_station_crs_origin_unique
        UNIQUE (train_service_id, train_station_id, origin),
    FOREIGN KEY (train_service_id)
        REFERENCES train_service(service_id)
        ON DELETE CASCADE,
    FOREIGN KEY (train_station_id) REFERENCES train_station(station_crs)
);

CREATE TABLE train_call (
    call_id SERIAL PRIMARY KEY,
    train_service_id INT NOT NULL,
    train_station_id INT NOT NULL,
    platform TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    mileage NUMERIC,
    CONSTRAINT train_call_unique_arr
        UNIQUE (train_service_id, run_date, station_crs, plan_arr),
    CONSTRAINT train_call_unique_dep
        UNIQUE (train_service_id, run_date, station_crs, plan_dep),
    FOREIGN KEY (train_service_id)
        REFERENCES train_service(service_id)
        ON DELETE CASCADE,
    FOREIGN KEY (train_station_id) REFERENCES train_station(station_id),
    CONSTRAINT mileage_positive CHECK (mileage >= 0)
);

CREATE TABLE train_associated_service_type (
    associated_type_id SERIAL PRIMARY KEY,
    type_name TEXT NOT NULL UNIQUE
);

INSERT INTO train_associated_service_type(associated_type_id, type_name)
VALUES (1, 'THIS_JOINS');

INSERT INTO train_associated_service_type(associated_type_id, type_name)
VALUES (2, 'OTHER_JOINS');

INSERT INTO train_associated_service_type(associated_type_id, type_name)
VALUES (3, 'THIS_DIVIDES');

INSERT INTO train_associated_service_type(associated_type_id, type_name)
VALUES (4, 'OTHER_DIVIDES');

CREATE TABLE train_associated_service (
    call_id INTEGER NOT NULL,
    associated_service_id INT NOT NULL,
    associated_type TEXT NOT NULL,
    FOREIGN KEY (associated_type)
        REFERENCES train_associated_service_type(associated_type),
    FOREIGN KEY (call_id)
        REFERENCES train_call(call_id)
        ON DELETE CASCADE,
    FOREIGN KEY (associated_service_id)
        REFERENCES train_service(train_service_id)
        ON DELETE CASCADE,
    CONSTRAINT train_associated_service_unique_call_service_type
        UNIQUE (call_id, associated_service_id, associated_type)
);

CREATE TABLE train_leg (
    train_leg_id SERIAL PRIMARY KEY,
    distance NUMERIC NOT NULL,
    CONSTRAINT distance_positive CHECK (distance > 0)
);

CREATE TABLE train_leg_call (
    leg_call_id SERIAL PRIMARY KEY,
    train_leg_id INTEGER NOT NULL,
    arr_call_id INTEGER,
    dep_call_id INTEGER,
    mileage NUMERIC,
    associated_type_id INTEGER,
    CONSTRAINT leg_call_unique UNIQUE (leg_id, arr_call_id, dep_call_id),
    FOREIGN KEY (leg_id) REFERENCES train_leg(leg_id) ON DELETE CASCADE,
    FOREIGN KEY (arr_call_id) REFERENCES train_call(call_id) ON DELETE CASCADE,
    FOREIGN KEY (dep_call_id) REFERENCES train_call(call_id) ON DELETE CASCADE,
    FOREIGN KEY (associated_type_id)
        REFERENCES train_associated_service_type(associated_type_id),
    CONSTRAINT mileage_positive CHECK (mileage >= 0),
    CONSTRAINT arr_or_dep CHECK (num_nulls(arr_call_id, dep_call_id) <= 1)
);

CREATE TABLE train_stock_segment (
    stock_segment_id SERIAL PRIMARY KEY,
    start_call INTEGER NOT NULL,
    end_call INTEGER NOT NULL,
    FOREIGN KEY (start_call) REFERENCES train_call(call_id) ON DELETE CASCADE,
    FOREIGN KEY (end_call) REFERENCES train_call(call_id) ON DELETE CASCADE,
    CONSTRAINT stock_segment_unique UNIQUE (start_call, end_call)
);

CREATE OR REPLACE FUNCTION is_valid_stock_formation (
    stock_class INTEGER,
    stock_subclass INTEGER,
    stock_cars INT
) RETURNS BOOLEAN
LANGUAGE plpgsql
AS
$$
BEGIN
    IF stock_class IS NULL
    THEN
        RETURN TRUE;
    END IF;
    IF stock_subclass IS NULL
    THEN
        IF stock_cars IS NULL
        THEN
            RETURN EXISTS(
                SELECT * FROM public.train_stock_formation
                WHERE stock_class = stock_class
            );
        ELSE
            RETURN EXISTS(
                SELECT * FROM public.train_stock_formation
                WHERE stock_class = stock_class
                AND cars = stock_cars
            );
        END IF;
    END IF;
    RETURN EXISTS (
        SELECT * FROM public.train_stock_formation
        WHERE stock_class = stock_class
        AND stock_subclass = stock_subclass
        AND cars = stock_cars
    );
END;
$$;

CREATE TABLE train_stock_report (
    stock_report_id SERIAL PRIMARY KEY,
    stock_class INTEGER,
    stock_subclass INTEGER,
    stock_number INTEGER,
    stock_cars INTEGER,
    FOREIGN KEY (stock_class)
        REFERENCES train_stock(stock_class),
    FOREIGN KEY (stock_class, stock_subclass)
        REFERENCES train_stock_subclass(stock_class, stock_subclass),
    CONSTRAINT train_stock_report_check_valid_stock_formation
        CHECK
            (is_valid_stock_formation(stock_class, stock_subclass, stock_cars))
);

CREATE TABLE train_stock_segment_report (
    stock_segment_id INTEGER NOT NULL,
    stock_report_id INTEGER NOT NULL,
    FOREIGN KEY (stock_segment_id)
        REFERENCES train_stock_segment(stock_segment_id),
    FOREIGN KEY (stock_report_id)
        REFERENCES train_stock_report(stock_report_id)
);

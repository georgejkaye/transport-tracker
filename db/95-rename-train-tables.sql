-- rename tables to be prefixed with train

ALTER TABLE AssociatedService RENAME TO train_associated_service;
ALTER TABLE AssociatedType RENAME TO train_associated_service_type;
ALTER TABLE Brand RENAME TO train_brand;
ALTER TABLE Call RENAME TO train_call;
ALTER TABLE Leg RENAME TO train_leg;
ALTER TABLE LegCall RENAME TO train_leg_call;
ALTER TABLE Operator RENAME TO train_operator;
ALTER TABLE OperatorCode RENAME TO train_operator_code;
ALTER TABLE OperatorStock RENAME TO train_operator_stock;
ALTER TABLE Service RENAME TO train_service;
ALTER TABLE ServiceEndpoint RENAME TO train_service_endpoint;
ALTER TABLE Station RENAME TO train_station;
ALTER TABLE StationName RENAME TO train_station_name;
ALTER TABLE StationPoint RENAME TO train_station_point;
ALTER TABLE Stock RENAME TO train_stock;
ALTER TABLE StockFormation RENAME TO train_stock_formation;
ALTER TABLE StockReport RENAME TO train_stock_report;
ALTER TABLE StockSegment RENAME TO train_stock_segment;
ALTER TABLE StockSegmentReport RENAME TO train_stock_segment_report;
ALTER TABLE StockSubclass RENAME TO train_stock_subclass;

-- make operator code text

ALTER TABLE train_operator_code ALTER COLUMN operator_code TYPE TEXT;

ALTER TABLE train_operator_code
ADD CONSTRAINT train_operator_code_check_operator_code_format
CHECK(operator_code ~ '^[[:alpha:]]{2}$');

ALTER TABLE train_operator ALTER COLUMN operator_code TYPE TEXT;

ALTER TABLE train_brand ALTER COLUMN brand_code TYPE TEXT;

ALTER TABLE train_brand
ADD CONSTRAINT train_brand_check_brand_code
CHECK(brand_code ~ '^[[:alpha:]]{2}$');

-- make headcode text

ALTER TABLE train_service ALTER COLUMN headcode TYPE TEXT;

ALTER TABLE train_service
ADD CONSTRAINT train_service_check_headcode_length
CHECK (LENGTH(headcode) = 4);

-- alter train_service primary key

ALTER TABLE train_service_endpoint
DROP CONSTRAINT serviceendpoint_service_id_run_date_fkey;

ALTER TABLE train_call
DROP CONSTRAINT call_service_id_run_date_fkey;

ALTER TABLE train_associated_service
DROP CONSTRAINT associatedservice_associated_id_associated_run_date_fkey;

ALTER TABLE train_service DROP CONSTRAINT service_pkey;
ALTER TABLE train_service RENAME COLUMN service_id TO unique_identifier;
ALTER TABLE train_service ADD train_service_id SERIAL NOT NULL;

ALTER TABLE train_service
ADD CONSTRAINT train_service_pkey
PRIMARY KEY(train_service_id);

ALTER TABLE train_service
ADD CONSTRAINT train_service_unique_unique_identifier_run_date
UNIQUE (unique_identifier, run_date);

-- add new foreign key to train_service_endpoint

ALTER TABLE train_service_endpoint
RENAME COLUMN service_id TO unique_identifier;

ALTER TABLE train_service_endpoint ADD train_service_id INT;

UPDATE train_service_endpoint SET train_service_id = (
    SELECT train_service.service_id
    FROM train_service
    WHERE train_service.run_date = train_service_endpoint.run_date
    AND train_service.unique_identifier
        = train_service_endpoint.unique_identifier
);

ALTER TABLE train_service_endpoint ALTER COLUMN train_service_id SET NOT NULL;

ALTER TABLE train_service_endpoint
ADD CONSTRAINT train_service_endpoint_train_service_id_fkey
FOREIGN KEY(train_service_id) REFERENCES train_service(train_service_id);

ALTER TABLE train_service_endpoint DROP COLUMN unique_identifier;
ALTER TABLE train_service_endpoint DROP COLUMN run_date;

-- add new foreign key to train_call

ALTER TABLE train_call RENAME COLUMN service_id TO unique_identifier;
ALTER TABLE train_call ADD train_service_id INT;

UPDATE train_call SET train_service_id = (
    SELECT train_service.train_service_id
    FROM train_service
    WHERE train_service.run_date = train_call.run_date
    AND train_service.unique_identifier = train_call.unique_identifier
);

ALTER TABLE train_call ALTER COLUMN train_service_id SET NOT NULL;

ALTER TABLE train_call
ADD CONSTRAINT train_call_service_id_fkey
FOREIGN KEY(train_service_id) REFERENCES train_service(train_service_id);

ALTER TABLE train_call DROP COLUMN unique_identifier;
ALTER TABLE train_call DROP COLUMN run_date;

-- add new foreign key to trainassociatedservice

ALTER TABLE train_associated_service
RENAME COLUMN associated_id TO associated_unique_identifier;
ALTER TABLE train_associated_service ADD train_service_id INT;

UPDATE train_associated_service SET train_service_id = (
    SELECT train_service.train_service_id
    FROM train_service
    WHERE train_service.run_date
        = train_associated_service.associated_run_date
    AND train_service.unique_identifier
        = train_associated_service.associated_unique_identifier
);

ALTER TABLE train_associated_service
ALTER COLUMN train_service_id SET NOT NULL;

ALTER TABLE train_associated_service
ADD CONSTRAINT train_associated_service_associated_service_id_fkey
FOREIGN KEY(associated_service_id) REFERENCES train_service(train_service_id);

ALTER TABLE train_associated_service DROP COLUMN associated_unique_identifier;
ALTER TABLE train_associated_service DROP COLUMN associated_run_date;

--- make train_station.station_crs type text

ALTER TABLE train_station
ALTER COLUMN station_crs TYPE TEXT;

ALTER TABLE train_station
ADD CONSTRAINT train_station_check_station_crs
CHECK(station_crs ~ '^[[:alpha:]]{3}$');

ALTER TABLE train_station
ADD CONSTRAINT train_station_unique_station_crs UNIQUE(station_crs);

--- make station id primary key

ALTER TABLE train_station_name DROP CONSTRAINT stationname_station_crs_fkey;
ALTER TABLE train_station_point DROP CONSTRAINT stationpoint_station_crs_fkey;

ALTER TABLE train_service_endpoint
DROP CONSTRAINT serviceendpoint_station_crs_fkey;

ALTER TABLE train_call DROP CONSTRAINT call_station_crs_fkey;

ALTER TABLE train_station DROP CONSTRAINT station_pkey;
ALTER TABLE train_station ADD COLUMN train_station_id SERIAL;

ALTER TABLE train_station
ADD CONSTRAINT train_station_pkey
PRIMARY KEY(train_station_id);

---- add new foreign key to train_station_name

ALTER TABLE train_station_name ADD train_station_id INT;

UPDATE train_station_name SET train_station_id = (
    SELECT train_station.train_station_id
    FROM train_station
    WHERE train_station.station_crs = train_station_name.station_crs
);

ALTER TABLE train_station_name ALTER COLUMN train_station_id SET NOT NULL;

ALTER TABLE train_station_name
ADD CONSTRAINT train_station_name_station_id_fkey
FOREIGN KEY(train_station_id) REFERENCES train_station(train_station_id);

ALTER TABLE train_station_name DROP COLUMN station_crs;

---- add new foreign key to train_station_point

ALTER TABLE train_station_point ADD train_station_id INT;

UPDATE train_station_point SET train_station_id = (
    SELECT train_station.train_station_id FROM train_station
    WHERE train_station.station_crs = train_station_point.station_crs
);

ALTER TABLE train_station_point ALTER COLUMN train_station_id SET NOT NULL;

ALTER TABLE train_station_point
ADD CONSTRAINT train_station_point_station_id_fkey
FOREIGN KEY(train_station_id) REFERENCES train_station(train_station_id);

ALTER TABLE train_station_point DROP COLUMN station_crs;

---- add new foreign key to train_service_endpoint

ALTER TABLE train_service_endpoint ADD train_station_id INT;

UPDATE train_service_endpoint SET train_station_id = (
    SELECT train_station.train_station_id FROM train_station
    WHERE train_station.station_crs = train_service_endpoint.station_crs
);

ALTER TABLE train_service_endpoint ALTER COLUMN train_station_id SET NOT NULL;

ALTER TABLE train_service_endpoint
ADD CONSTRAINT train_service_endpoint_station_id_fkey
FOREIGN KEY(train_station_id) REFERENCES train_station(train_station_id);

ALTER TABLE train_service_endpoint DROP COLUMN station_crs;

---- add new foreign key to train_call

ALTER TABLE train_call ADD train_station_id INT;

UPDATE train_call SET train_station_id = (
    SELECT train_station.train_station_id FROM train_station
    WHERE train_station.station_crs = train_call.station_crs
);

ALTER TABLE train_call ALTER COLUMN train_station_id SET NOT NULL;

ALTER TABLE train_call
ADD CONSTRAINT train_call_station_id_fkey
FOREIGN KEY(train_station_id) REFERENCES train_station(train_station_id);

ALTER TABLE train_call DROP COLUMN station_crs;

-- Fix empty stock name

UPDATE train_stock SET name = NULL WHERE name = '';

-- Readd uniqueness constraint to train_service_endpoint

ALTER TABLE train_service_endpoint
ADD CONSTRAINT train_service_endpoint_unique_service_station_origin
UNIQUE (train_service_id, train_station_id, origin);

-- Readd uniqueness constraint to train_associated_service

ALTER TABLE train_associated_service
ADD CONSTRAINT train_associated_service_unique_call_service_type
UNIQUE (call_id, associated_service_id, associated_type);

-- Make associated type have ids

ALTER TABLE train_associated_service_type
ADD COLUMN train_associated_type_id SERIAL;

ALTER TABLE train_associated_service_type
RENAME COLUMN associated_type TO type_name;

ALTER TABLE train_associated_service_type
ADD CONSTRAINT train_associated_service_type_name_unique
UNIQUE (type_name);

ALTER TABLE train_associated_service_type
ALTER COLUMN type_name SET NOT NULL;

ALTER TABLE train_associated_service
DROP CONSTRAINT associatedservice_associated_type_fkey;

ALTER TABLE train_leg_call
DROP CONSTRAINT legcall_assoc_type_fkey;

ALTER TABLE train_associated_service_type
DROP CONSTRAINT associatedtype_pkey;

ALTER TABLE train_associated_service_type
ADD CONSTRAINT train_associated_service_type_pkey
PRIMARY KEY (train_associated_type_id);

ALTER TABLE train_associated_service
ADD COLUMN train_associated_type_id INTEGER;

ALTER TABLE train_associated_service
ADD CONSTRAINT train_associated_service_train_associated_type_id_fkey
FOREIGN KEY(train_associated_type_id)
REFERENCES train_associated_service_type(train_associated_type_id);

UPDATE train_associated_service
SET associated_type_id = (
    SELECT associated_type_id
    FROM train_associated_service_type
    WHERE type_name = associated_type
);

ALTER TABLE train_associated_service
ALTER COLUMN associated_type_id SET NOT NULL;

ALTER TABLE train_associated_service
DROP COLUMN associated_type;

ALTER TABLE train_leg_call
ADD COLUMN associated_type_id INTEGER;

ALTER TABLE train_leg_call
ADD CONSTRAINT train_leg_call_associated_type_id_fkey
FOREIGN KEY(associated_type_id)
REFERENCES train_associated_service_type(associated_type_id);

UPDATE train_leg_call
SET associated_type_id = (
    SELECT associated_type_id
    FROM train_associated_service_type
    WHERE type_name = assoc_type
);

ALTER TABLE train_leg_call
DROP COLUMN assoc_type;

UPDATE train_associated_service_type
SET type_name = 'THIS_JOINS'
WHERE type_name = 'JOINS_TO';

UPDATE train_associated_service_type
SET type_name = 'OTHER_JOINS'
WHERE type_name = 'JOINS_WITH';

UPDATE train_associated_service_type
SET type_name = 'THIS_DIVIDES'
WHERE type_name = 'DIVIDES_TO';

UPDATE train_associated_service_type
SET type_name = 'OTHER_DIVIDES'
WHERE type_name = 'DIVIDES_FROM';

-- split train sequence and train leg

ALTER TABLE traveller
RENAME TO transport_user;

CREATE TABLE transport_user_train_leg (
    transport_user_train_leg_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    train_leg_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES transport_user(user_id),
    FOREIGN KEY (train_leg_id)
        REFERENCES train_leg(train_leg_id)
);

INSERT INTO transport_user_train_leg (user_id, train_leg_id)
SELECT user_id, train_leg_id FROM train_leg;

ALTER TABLE train_leg
DROP COLUMN user_id;

-- put train in front of primary ids

ALTER TABLE train_operator
RENAME operator_id TO train_operator_id;

ALTER TABLE train_brand
RENAME brand_id TO train_brand_id;

ALTER TABLE train_brand
RENAME parent_operator TO train_operator_id;

ALTER TABLE train_operator_stock
RENAME operator_id TO train_operator_id;

ALTER TABLE train_operator_stock
RENAME brand_id TO train_brand_id;

ALTER TABLE train_station
RENAME operator_id TO train_operator_id;

ALTER TABLE train_station
RENAME brand_id TO train_brand_id;

ALTER TABLE train_service
RENAME operator_id TO train_operator_id;

ALTER TABLE train_service
RENAME brand_id TO train_brand_id;

ALTER TABLE train_brand
RENAME brand_id TO train_brand_id;

ALTER TABLE train_call
RENAME call_id TO train_call_id;

ALTER TABLE train_leg
RENAME leg_id TO train_leg_id;

ALTER TABLE train_leg_call
RENAME leg_id TO train_leg_id;

ALTER TABLE train_stock_segment
RENAME stock_segment_id TO train_stock_segment_id;

ALTER TABLE train_stock_report
RENAME stock_report_id TO train_stock_report_id;

ALTER TABLE train_stock_segment_report
RENAME stock_segment_id TO train_stock_segment_id;

ALTER TABLE train_stock_segment_report
RENAME stock_report_id TO train_stock_report_id;

-- fix brand constraint

ALTER TABLE train_service
DROP CONSTRAINT valid_brand;

ALTER TABLE train_operator_stock
DROP CONSTRAINT valid_brand;

DROP FUNCTION isvalidbrand;

CREATE OR REPLACE FUNCTION is_valid_brand(
    p_brand_id INTEGER,
    p_operator_id INTEGER
) RETURNS BOOLEAN
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN p_brand_id IS NULL
        OR (
            SELECT train_operator_id FROM train_brand
            WHERE train_brand_id = p_brand_id
        ) = p_operator_id;
END;
$$;

ALTER TABLE train_service
ADD CONSTRAINT train_service_check_is_valid_brand
CHECK (is_valid_brand(train_brand_id, train_operator_id));

ALTER TABLE train_operator_stock
ADD CONSTRAINT train_operator_stock_check_is_valid_brand
CHECK (is_valid_brand(train_brand_id, train_operator_id));

-- isvalidstockformation constraint

ALTER TABLE train_stock_report
DROP CONSTRAINT valid_stock;

DROP FUNCTION isvalidstockformation;

CREATE OR REPLACE FUNCTION is_valid_stock_formation (
    p_stock_class INTEGER,
    p_stock_subclass INTEGER,
    p_stock_cars INT
) RETURNS BOOLEAN
LANGUAGE plpgsql
AS
$$
BEGIN
    IF p_stock_class IS NULL
    THEN
        RETURN TRUE;
    END IF;
    IF p_stock_subclass IS NULL
    THEN
        IF p_stock_cars IS NULL
        THEN
            RETURN EXISTS(
                SELECT * FROM public.train_stock_formation
                WHERE stock_class = p_stock_class
            );
        ELSE
            RETURN EXISTS(
                SELECT * FROM public.train_stock_formation
                WHERE stock_class = p_stock_class
                AND cars = p_stock_cars
            );
        END IF;
    END IF;
    RETURN EXISTS (
        SELECT * FROM public.train_stock_formation
        WHERE stock_class = p_stock_class
        AND stock_subclass = p_stock_subclass
        AND cars = p_stock_cars
    );
END;
$$;

ALTER TABLE train_stock_report
ADD CONSTRAINT train_stock_report_check_valid_stock_formation
CHECK (is_valid_stock_formation(stock_class, stock_subclass, stock_cars));

-- add call constraint

ALTER TABLE train_call
ADD CONSTRAINT train_call_unique_service_station_arr_dep
    UNIQUE NULLS NOT DISTINCT (
        train_service_id,
        train_station_id,
        plan_arr,
        act_arr,
        plan_dep,
        act_dep);

-- drop old user data types

DROP TYPE useroutdata CASCADE;
DROP TYPE useroutpublicdata CASCADE;
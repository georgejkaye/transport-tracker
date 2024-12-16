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

CREATE TYPE OperatorData AS (
    operator_id INTEGER,
    operator_code CHARACTER(2),
    operator_name TEXT,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE OR REPLACE FUNCTION GetOperatorId(
    p_operator_code CHARACTER(2),
    p_run_date TIMESTAMP WITH TIME ZONE
)
RETURNS INTEGER
LANGUAGE plpgsql
AS
$$
DECLARE
    v_operator_id INTEGER;
BEGIN
    SELECT operator_id INTO v_operator_id FROM Operator
    WHERE operator_code = p_operator_code
    AND operation_range @> p_run_date::date;
    RETURN v_operator_id;
END;
$$;

CREATE TABLE Brand (
    brand_id SERIAL PRIMARY KEY,
    brand_code CHARACTER(2),
    brand_name TEXT NOT NULL,
    parent_operator INTEGER NOT NULL,
    bg_colour TEXT,
    fg_colour TEXT,
    FOREIGN KEY (parent_operator) REFERENCES Operator(operator_id)
);

CREATE TYPE BrandData AS (
    brand_id INTEGER,
    brand_code CHARACTER(2).
    brand_name TEXT
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE OR REPLACE FUNCTION GetBrandId(
    p_brand_code CHARACTER(2),
    p_run_date TIMESTAMP WITH TIME ZONE
)
RETURNS INTEGER
LANGUAGE plpgsql
AS
$$
DECLARE
    v_brand_id INTEGER;
BEGIN
    SELECT brand_id INTO v_brand_id
    FROM Brand
    INNER JOIN Operator
    ON Operator.operator_id = Brand.parent_operator
    WHERE brand_code = p_brand_code
    AND operation_range @> p_run_date::date;
    RETURN v_brand_id;
END;
$$;

CREATE OR REPLACE FUNCTION validBrand(
    p_brand_id INTEGER,
    p_operator_id INTEGER
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

CREATE TABLE Stock (
    stock_class INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE StockSubclass (
    stock_class INTEGER NOT NULL,
    stock_subclass INTEGER NOT NULL,
    name TEXT,
    PRIMARY KEY (stock_class, stock_subclass),
    FOREIGN KEY (stock_class) REFERENCES Stock(stock_class)
);

CREATE TABLE StockFormation (
    stock_class INTEGER NOT NULL,
    stock_subclass INTEGER,
    cars INTEGER NOT NULL,
    FOREIGN KEY (stock_class) REFERENCES Stock(stock_class),
    FOREIGN KEY (stock_class, stock_subclass) REFERENCES StockSubclass(stock_class, stock_subclass),
    CONSTRAINT stock_class_cars_unique UNIQUE (stock_class, stock_subclass, cars)
);

CREATE TABLE OperatorStock (
    operator_id INTEGER NOT NULL,
    brand_id INTEGER,
    stock_class INTEGER NOT NULL,
    stock_subclass INTEGER,
    FOREIGN KEY (operator_id) REFERENCES Operator(operator_id),
    FOREIGN KEY (brand_id) REFERENCES Brand(brand_id),
    FOREIGN KEY (stock_class) REFERENCES Stock(stock_class),
    FOREIGN KEY (stock_class, stock_subclass) REFERENCES StockSubclass(stock_class, stock_subclass),
    CONSTRAINT operator_stock_classes_unique UNIQUE NULLS NOT DISTINCT (operator_id, brand_id, stock_class, stock_subclass),
    CONSTRAINT valid_brand CHECK (validBrand(brand_id, operator_id))
);

CREATE TABLE Station (
    station_crs CHARACTER(3) PRIMARY KEY,
    station_name TEXT NOT NULL,
    operator_id INTEGER NOT NULL,
    brand_id INTEGER,
    station_img TEXT,
    FOREIGN KEY (operator_id) REFERENCES Operator(operator_id),
    FOREIGN KEY (brand_id) REFERENCES Brand(brand_id),
    CONSTRAINT valid_brand CHECK (validBrand(brand_id, operator_id))
);

CREATE TABLE Service (
    service_id TEXT NOT NULL,
    run_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    headcode CHARACTER(4) NOT NULL,
    operator_id INTEGER NOT NULL,
    brand_id INTEGER,
    power TEXT,
    PRIMARY KEY (service_id, run_date),
    FOREIGN KEY (operator_id) REFERENCES Operator(operator_id),
    FOREIGN KEY (brand_id) REFERENCES Brand(brand_id),
    CONSTRAINT valid_brand CHECK (validBrand(brand_id, operator_id))
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
    call_id INTEGER NOT NULL,
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
    leg_id INTEGER NOT NULL,
    arr_call_id INTEGER,
    dep_call_id INTEGER,
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

CREATE OR REPLACE FUNCTION GetCallFromLegCall (
    p_service_id TEXT,
    p_run_date TIMESTAMP WITH TIME ZONE,
    p_station_crs CHARACTER(3),
    p_plan_arr TIMESTAMP WITH TIME ZONE,
    p_plan_dep TIMESTAMP WITH TIME ZONE,
    p_act_arr TIMESTAMP WITH TIME ZONE,
    p_act_dep TIMESTAMP WITH TIME ZONE
) RETURNS INTEGER
LANGUAGE plpgsql
AS
$$
DECLARE
    v_call_id INTEGER;
BEGIN
    IF p_service_id IS NULL THEN
        RETURN NULL;
    ELSE
        SELECT call_id INTO v_call_id
        FROM Call
        WHERE service_id = p_service_id
        AND run_date = p_run_date
        AND station_crs = p_station_crs
        AND
            COALESCE(plan_arr, plan_dep, act_arr, act_dep) =
            COALESCE(p_plan_arr, p_plan_dep, p_act_arr, p_act_dep);
        IF v_call_id IS NULL THEN
            RAISE 'Call not found for service id %, run date %, station crs %, plan arr %, plan dep %, act arr %, act dep %',
                    p_service_id, p_run_date, p_station_crs, p_plan_arr,
                    p_plan_dep, p_act_arr, p_act_dep;
        END IF;
        RETURN v_call_id;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION validStockFormation (
    stockclass INTEGER,
    stocksubclass INTEGER,
    stockcars INTEGER
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

CREATE TABLE StockSegment (
    stock_segment_id SERIAL PRIMARY KEY,
    start_call INTEGER NOT NULL,
    end_call INTEGER NOT NULL,
    FOREIGN KEY (start_call) REFERENCES Call(call_id) ON DELETE CASCADE,
    FOREIGN KEY (end_call) REFERENCES Call(call_id) ON DELETE CASCADE,
    CONSTRAINT stock_segment_unique UNIQUE (start_call, end_call)
);

CREATE OR REPLACE FUNCTION GetStockSegmentId (
    p_start_call INTEGER,
    p_end_call INTEGER
) RETURNS INTEGER
LANGUAGE plpgsql
AS
$$
DECLARE
    v_stock_segment_id INTEGER;
BEGIN
    SELECT stock_segment_id INTO v_stock_segment_id
    FROM StockSegment
    WHERE start_call = p_start_call
    AND end_call = p_end_call;
    IF v_stock_segment_id IS NULL THEN
        RAISE 'Could not find stock segment for start call % and end call %', p_start_call, p_end_call;
    END IF;
    RETURN v_stock_segment_id;
END;
$$;

CREATE TABLE StockReport (
    stock_report_id SERIAL PRIMARY KEY,
    stock_class INTEGER,
    stock_subclass INTEGER,
    stock_number INTEGER,
    stock_cars INTEGER,
    FOREIGN KEY (stock_class) REFERENCES Stock(stock_class),
    FOREIGN KEY (stock_class, stock_subclass) REFERENCES StockSubclass(stock_class, stock_subclass),
    CONSTRAINT valid_stock CHECK (validStockFormation(stock_class, stock_subclass, stock_cars))
);

CREATE OR REPLACE FUNCTION GetStockReportId (
    p_stock_class INTEGER,
    p_stock_subclass INTEGER,
    p_stock_number INTEGER,
    p_stock_cars INTEGER
) RETURNS INTEGER
LANGUAGE plpgsql
AS
$$
DECLARE
    v_stock_report_id INTEGER;
BEGIN
    SELECT stock_report_id INTO v_stock_report_id
    FROM StockReport
    WHERE (p_stock_class IS NULL AND stock_class IS NULL) OR (stock_class = p_stock_class)
    AND (p_stock_subclass IS NULL AND stock_subclass IS NULL) OR (stock_subclass = p_stock_subclass)
    AND (p_stock_number IS NULL AND stock_number IS NULL) OR (stock_number = p_stock_number)
    AND (p_stock_cars IS NULL AND stock_cars IS NULL) OR (stock_cars = p_stock_cars);
    IF v_stock_report_id IS NULL THEN
        RAISE 'Could not find stock report for class % subclass % number % cars %', p_stock_class, p_stock_subclass, p_stock_number, p_stock_cars;
    END IF;
    RETURN v_stock_report_id;
END;
$$;

CREATE TABLE StockSegmentReport (
    stock_segment_id INTEGER NOT NULL,
    stock_report_id INTEGER NOT NULL,
    FOREIGN KEY (stock_segment_id) REFERENCES StockSegment(stock_segment_id),
    FOREIGN KEY (stock_report_id) REFERENCES StockReport(stock_report_id)
);

CREATE TYPE service_data AS (
    service_id TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    headcode CHARACTER(4),
    operator_code CHARACTER(2),
    brand_code CHARACTER(2),
    power TEXT
);

CREATE TYPE endpoint_data AS (
    service_id TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    station_crs CHARACTER(3),
    origin BOOLEAN
);

CREATE TYPE call_data AS (
    service_id TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    station_crs CHARACTER(3),
    platform TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    mileage DECIMAL
);

CREATE TYPE assoc_data AS (
    service_id TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    station_crs CHARACTER(3),
    plan_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    assoc_id TEXT,
    assoc_run_date TIMESTAMP WITH TIME ZONE,
    assoc_type TEXT
);

CREATE OR REPLACE FUNCTION InsertServices(
    p_services service_data[],
    p_endpoints endpoint_data[],
    p_calls call_data[],
    p_assocs assoc_data[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
DECLARE
    v_operator_id INTEGER;
    v_brand_id INTEGER;
BEGIN
    INSERT INTO Service(
        service_id,
        run_date,
        headcode,
        operator_id,
        brand_id,
        power
    ) SELECT
        v_service.service_id,
        v_service.run_date,
        v_service.headcode,
        (SELECT GetOperatorId(v_service.operator_code, v_service.run_date)),
        (SELECT GetBrandId(v_service.brand_code, v_service.run_date)),
        v_service.power
    FROM UNNEST(p_services) AS v_service
    ON CONFLICT DO NOTHING;
    INSERT INTO ServiceEndpoint(
        service_id,
        run_date,
        station_crs,
        origin
    ) SELECT
        v_endpoint.service_id,
        v_endpoint.run_date,
        v_endpoint.station_crs,
        v_endpoint.origin
    FROM UNNEST(p_endpoints) AS v_endpoint
    ON CONFLICT DO NOTHING;
    INSERT INTO Call(
        service_id,
        run_date,
        station_crs,
        platform,
        plan_arr,
        plan_dep,
        act_arr,
        act_dep,
        mileage
    ) SELECT
        v_call.service_id,
        v_call.run_date,
        v_call.station_crs,
        v_call.platform,
        v_call.plan_arr,
        v_call.plan_dep,
        v_call.act_arr,
        v_call.act_dep,
        v_call.mileage
    FROM UNNEST(p_calls) AS v_call
    ON CONFLICT DO NOTHING;
    INSERT INTO AssociatedService(
        call_id,
        associated_id,
        associated_run_date,
        associated_type
    ) SELECT
        (SELECT GetCallFromLegCall(
            v_assoc.service_id,
            v_assoc.run_date,
            v_assoc.station_crs,
            v_assoc.plan_arr,
            v_assoc.plan_dep,
            v_assoc.act_arr,
            v_assoc.act_dep
        )),
        v_assoc.assoc_id,
        v_assoc.assoc_run_date,
        v_assoc.assoc_type
    FROM UNNEST(p_assocs) AS v_assoc
    ON CONFLICT DO NOTHING;
END;
$$;

CREATE TYPE leg_data AS (
    distance DECIMAL
);

CREATE TYPE legcall_call_data AS (
    service_id TEXT,
    call_run_date TIMESTAMP WITH TIME ZONE,
    call_station_crs CHARACTER(3),
    call_plan_arr TIMESTAMP WITH TIME ZONE,
    call_plan_dep TIMESTAMP WITH TIME ZONE,
    call_act_arr TIMESTAMP WITH TIME ZONE,
    call_act_dep TIMESTAMP WITH TIME ZONE
);

CREATE TYPE legcall_data AS (
    arr_call_service_id TEXT,
    arr_call_run_date TIMESTAMP WITH TIME ZONE,
    arr_call_station_crs CHARACTER(3),
    arr_call_plan_arr TIMESTAMP WITH TIME ZONE,
    arr_call_plan_dep TIMESTAMP WITH TIME ZONE,
    arr_call_act_arr TIMESTAMP WITH TIME ZONE,
    arr_call_act_dep TIMESTAMP WITH TIME ZONE,
    dep_call_service_id TEXT,
    dep_call_run_date TIMESTAMP WITH TIME ZONE,
    dep_call_station_crs CHARACTER(3),
    dep_call_plan_arr TIMESTAMP WITH TIME ZONE,
    dep_call_plan_dep TIMESTAMP WITH TIME ZONE,
    dep_call_act_arr TIMESTAMP WITH TIME ZONE,
    dep_call_act_dep TIMESTAMP WITH TIME ZONE,
    mileage DECIMAL,
    assoc_type TEXT
);

CREATE TYPE stockreport_data AS (
    arr_call_service_id TEXT,
    arr_call_run_date TIMESTAMP WITH TIME ZONE,
    arr_call_station_crs CHARACTER(3),
    arr_call_plan_arr TIMESTAMP WITH TIME ZONE,
    arr_call_plan_dep TIMESTAMP WITH TIME ZONE,
    arr_call_act_arr TIMESTAMP WITH TIME ZONE,
    arr_call_act_dep TIMESTAMP WITH TIME ZONE,
    dep_call_service_id TEXT,
    dep_call_run_date TIMESTAMP WITH TIME ZONE,
    dep_call_station_crs CHARACTER(3),
    dep_call_plan_arr TIMESTAMP WITH TIME ZONE,
    dep_call_plan_dep TIMESTAMP WITH TIME ZONE,
    dep_call_act_arr TIMESTAMP WITH TIME ZONE,
    dep_call_act_dep TIMESTAMP WITH TIME ZONE,
    stock_class INTEGER,
    stock_subclass INTEGER,
    stock_number INTEGER,
    stock_cars INTEGER
);

CREATE OR REPLACE FUNCTION InsertLeg(
    p_leg_distance DECIMAL,
    p_legcalls legcall_data[],
    p_stockreports stockreport_data[]
)
RETURNS VOID
LANGUAGE plpgsql
AS
$$
DECLARE
    v_leg_id INTEGER;
BEGIN
    INSERT INTO Leg(distance)
        VALUES (p_leg_distance)
        RETURNING leg_id INTO v_leg_id;
    INSERT INTO LegCall(leg_id, arr_call_id, dep_call_id, mileage, assoc_type)
        SELECT
            v_leg_id,
            (SELECT GetCallFromLegCall(
                v_legcall.arr_call_service_id,
                v_legcall.arr_call_run_date,
                v_legcall.arr_call_station_crs,
                v_legcall.arr_call_plan_arr,
                v_legcall.arr_call_plan_dep,
                v_legcall.arr_call_act_arr,
                v_legcall.arr_call_act_dep
            )),
            (SELECT GetCallFromLegCall(
                v_legcall.dep_call_service_id,
                v_legcall.dep_call_run_date,
                v_legcall.dep_call_station_crs,
                v_legcall.dep_call_plan_arr,
                v_legcall.dep_call_plan_dep,
                v_legcall.dep_call_act_arr,
                v_legcall.dep_call_act_dep
            )),
            v_legcall.mileage,
            v_legcall.assoc_type
        FROM UNNEST(p_legcalls) AS v_legcall;
    INSERT INTO StockSegment(start_call, end_call)
        SELECT
            (SELECT GetCallFromLegCall(
                v_stockreport.arr_call_service_id,
                v_stockreport.arr_call_run_date,
                v_stockreport.arr_call_station_crs,
                v_stockreport.arr_call_plan_arr,
                v_stockreport.arr_call_plan_dep,
                v_stockreport.arr_call_act_arr,
                v_stockreport.arr_call_act_dep
            )),
            (SELECT GetCallFromLegCall(
                v_stockreport.dep_call_service_id,
                v_stockreport.dep_call_run_date,
                v_stockreport.dep_call_station_crs,
                v_stockreport.dep_call_plan_arr,
                v_stockreport.dep_call_plan_dep,
                v_stockreport.dep_call_act_arr,
                v_stockreport.dep_call_act_dep
            ))
        FROM UNNEST(p_stockreports) AS v_stockreport;
    INSERT INTO StockReport(
        stock_class,
        stock_subclass,
        stock_number,
        stock_cars
    ) SELECT
        v_stockreport.stock_class,
        v_stockreport.stock_subclass,
        v_stockreport.stock_number,
        v_stockreport.stock_cars
    FROM UNNEST(p_stockreports) AS v_stockreport
    ON CONFLICT DO NOTHING;
    INSERT INTO StockSegmentReport(
        stock_segment_id,
        stock_report_id
    ) SELECT
        (SELECT GetStockSegmentId(
            (SELECT GetCallFromLegCall(
                v_stockreport.arr_call_service_id,
                v_stockreport.arr_call_run_date,
                v_stockreport.arr_call_station_crs,
                v_stockreport.arr_call_plan_arr,
                v_stockreport.arr_call_plan_dep,
                v_stockreport.arr_call_act_arr,
                v_stockreport.arr_call_act_dep
            )),
            (SELECT GetCallFromLegCall(
                v_stockreport.dep_call_service_id,
                v_stockreport.dep_call_run_date,
                v_stockreport.dep_call_station_crs,
                v_stockreport.dep_call_plan_arr,
                v_stockreport.dep_call_plan_dep,
                v_stockreport.dep_call_act_arr,
                v_stockreport.dep_call_act_dep
            ))
        )),
        (SELECT GetStockReportId(
            v_stockreport.stock_class,
            v_stockreport.stock_subclass,
            v_stockreport.stock_number,
            v_stockreport.stock_cars
        ))
    FROM UNNEST(p_stockreports) AS v_stockreport
    ON CONFLICT DO NOTHING;
END;
$$;

CREATE TYPE StockData AS (
    stock_class INT,
    stock_subclass INT,
    stock_number INT,
    stock_cars INT
)

CREATE TYPE StationLegData AS (
    platform TEXT,
    leg_id INTEGER,
    board_name TEXT,
    board_crs CHARACTER(3),
    alight_name TEXT,
    alight_crs CHARACTER(3),
    stop_time TIMESTAMP WITH TIME ZONE,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    calls_before INTEGER,
    calls_after INTEGER,
    operator OperatorData,
    brand BrandData,
    stock StockData[]
)

CREATE TYPE StationEndpointData AS (
    station_name TEXT,
    station_crs CHARACTER(3),
    boards INTEGER,
    alights INTEGER,
    calls INTEGER,
    operator OperatorData,
    brand BrandData,
    legs StationLegData
)

CREATE OR REPLACE FUNCTION GetStartTime (
    p_leg_id NUMBER
) RETURNS TIMESTAMP WITH TIME ZONE
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN
        SELECT MIN(COALESCE(plan_dep, act_dep, plan_arr, act_arr))
        FROM Call
        INNER JOIN LegCall
        ON Call.call_id = LegCall.arr_call_id
        OR Call.call_id = LegCall.dep_call_id
        INNER JOIN Leg
        ON Leg.leg_id = LegCall.leg_id

CREATE OR REPLACE FUNCTION GetStationBoards ()
RETURNS TABLE (station_crs CHARACTER(3), boards BIGINT)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
        SELECT Call.station_crs, COALESCE(COUNT(*), '0') AS boards
        FROM Leg
        INNER JOIN (
            SELECT
                Leg.leg_id,
                MIN(COALESCE(Call.plan_dep, Call.act_dep)) as last
            FROM Leg
            INNER JOIN LegCall
            ON Leg.leg_id = LegCall.leg_id
            INNER JOIN Call
            ON Call.call_id = LegCall.arr_call_id
            OR Call.call_id = LegCall.dep_call_id
            GROUP BY Leg.leg_id
        ) LegFirstCall
        ON LegFirstCall.leg_id = Leg.leg_id
        INNER JOIN Call
        ON LegFirstCall.last = COALESCE(Call.plan_dep, Call.act_dep, Call.plan_arr, Call.act_arr)
        GROUP BY Call.station_crs;
END;
$$;

CREATE OR REPLACE FUNCTION GetStationAlights ()
RETURNS TABLE (station_crs CHARACTER(3), alights BIGINT)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
        SELECT Call.station_crs, COALESCE(COUNT(*), '0') AS boards
        FROM Leg
        INNER JOIN (
            SELECT
                Leg.leg_id,
                MAX(COALESCE(Call.plan_dep, Call.act_dep)) as last
            FROM Leg
            INNER JOIN LegCall
            ON Leg.leg_id = LegCall.leg_id
            INNER JOIN Call
            ON Call.call_id = LegCall.arr_call_id
            OR Call.call_id = LegCall.dep_call_id
            GROUP BY Leg.leg_id
        ) LegLastCall
        ON LegLastCall.leg_id = Leg.leg_id
        INNER JOIN Call
        ON LegLastCall.last = COALESCE(Call.plan_dep, Call.act_dep, Call.plan_arr, Call.act_arr)
        GROUP BY Call.station_crs;
END;
$$;

CREATE OR REPLACE FUNCTION GetStationCalls ()
RETURNS TABLE (station_crs CHARACTER(3), calls BIGINT)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
        SELECT Call.station_crs, COUNT(*) AS calls
        FROM Call
        GROUP BY Call.station_crs;
END;
$$;

CREATE OR REPLACE FUNCTION GetStation (
    p_station_crs CHARACTER(3)
) RETURNS StationData
LANGUAGE plpgsql
AS
$$
DECLARE
    v_boards INTEGER
BEGIN
    SELECT ARRAY_AGG(leg_id), COALESCE(COUNT(*), 0) INTO v_boards
    FROM Call
    INNER JOIN LegCall
    ON LegCall.arr_call_id = Call.call_id
    OR LegCall.dep_call_id = Call.call_id
    INNER JOIN (
        SELECT

            MIN(COALESCE(Call.plan_dep, Call.act_dep, Call.plan_arr, Call.act_arr)) AS call_time
        FROM Leg
        INNER JOIN LegCall
        ON Leg.leg_id = LegCall.leg_id
        INNER JOIN Call
        ON LegCall.arr_call_id = Call.call_id
        OR LegCall.dep_call_id = Call.call_id
        GROUP BY Leg.leg_id
    ) FirstCallTime
    ON COALESCE(Call.plan_dep, Call.act_dep, Call.plan)
    WHERE Call.station_crs = p_station_crs;
END;
$$;
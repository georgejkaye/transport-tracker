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

CREATE OR REPLACE FUNCTION GetOperatorId(
    p_operator_code CHARACTER(2),
    p_run_date TIMESTAMP WITH TIME ZONE
)
RETURNS INT
LANGUAGE plpgsql
AS
$$
DECLARE
    v_operator_id INT;
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

CREATE OR REPLACE FUNCTION GetBrandId(
    p_brand_code CHARACTER(2),
    p_run_date TIMESTAMP WITH TIME ZONE
)
RETURNS INT
LANGUAGE plpgsql
AS
$$
DECLARE
    v_brand_id INT;
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

CREATE TABLE StockSegment (
    stock_segment_id SERIAL PRIMARY KEY,
    start_call INT NOT NULL,
    end_call INT NOT NULL,
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
    stock_class INT,
    stock_subclass INT,
    stock_number INT,
    stock_cars INT,
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
    WHERE ((p_stock_class IS NULL AND stock_class IS NULL) OR (stock_class = p_stock_class))
    AND ((p_stock_subclass IS NULL AND stock_subclass IS NULL) OR (stock_subclass = p_stock_subclass))
    AND ((p_stock_number IS NULL AND stock_number IS NULL) OR (stock_number = p_stock_number))
    AND ((p_stock_cars IS NULL AND stock_cars IS NULL) OR (stock_cars = p_stock_cars));
    IF v_stock_report_id IS NULL THEN
        RAISE 'Could not find stock report for class % subclass % number % cars %', p_stock_class, p_stock_subclass, p_stock_number, p_stock_cars;
    END IF;
    RETURN v_stock_report_id;
END;
$$;

CREATE TABLE StockSegmentReport (
    stock_segment_id INT NOT NULL,
    stock_report_id INT NOT NULL,
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
    v_operator_id INT;
    v_brand_id INT;
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
    stock_class INT,
    stock_subclass INT,
    stock_number INT,
    stock_cars INT
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
    v_leg_id INT;
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
        FROM UNNEST(p_stockreports) AS v_stockreport
        ON CONFLICT DO NOTHING;
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

CREATE TYPE OutOperatorData AS (
    operator_id INTEGER,
    operator_code TEXT,
    operator_name TEXT,
    operator_bg TEXT,
    operator_fg TEXT
);

CREATE TYPE OutServiceStationData AS (
    station_crs CHARACTER(3),
    station_name TEXT
);

CREATE TYPE OutServiceAssocData AS (
    assoc_service_id TEXT,
    assoc_service_run_date TIMESTAMP WITH TIME ZONE,
    assoc_type TEXT
);

CREATE OR REPLACE FUNCTION GetCallAssocData()
RETURNS TABLE (call_id INTEGER, call_assocs OutServiceAssocData[])
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH assocs AS (
        SELECT
            AssocData.call_id,
            (associated_id, associated_run_date, associated_type)::OutServiceAssocData AS call_assocs
        FROM (
            SELECT
                AssociatedService.call_id,
                AssociatedService.associated_id,
                AssociatedService.associated_run_date,
                AssociatedService.associated_type
            FROM AssociatedService
        ) AssocData
    )
    SELECT
        assocs.call_id,
        ARRAY_AGG(assocs.call_assocs) AS associations
    FROM assocs
    GROUP BY assocs.call_id;
END;
$$;

CREATE TYPE OutServiceCallData AS (
    station OutServiceStationData,
    platform TEXT,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    assocs OutServiceAssocData[],
    mileage DECIMAL
);

CREATE TYPE OutServiceData AS (
    service_id TEXT,
    service_headcode CHARACTER(4),
    service_run_date TIMESTAMP WITH TIME ZONE,
    service_service_start TIMESTAMP WITH TIME ZONE,
    service_origins OutServiceStationData[],
    service_destinations OutServiceStationData[],
    service_operator OutOperatorData,
    service_brand OutOperatorData,
    service_calls OutServiceCallData[],
    service_assocs OutServiceAssocData[]
);

CREATE TYPE OutStockData AS (
    stock_class INTEGER,
    stock_subclass INTEGER,
    stock_number INTEGER,
    stock_cars INTEGER
);

CREATE OR REPLACE FUNCTION GetCallStockInfo()
RETURNS TABLE (start_call INTEGER, stock_info OutStockData[])
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH call_stock_data AS (
        SELECT
            CallStock.start_call,
            (stock_class, stock_subclass, stock_number, stock_cars)::OutStockData AS stock_data
        FROM (
            SELECT StockSegment.start_call, stock_class, stock_subclass,
                stock_number, stock_cars
            FROM StockSegment
            INNER JOIN StockSegmentReport
            ON StockSegment.stock_segment_id = StockSegmentReport.stock_segment_id
            INNER JOIN StockReport
            ON StockSegmentReport.stock_report_id = StockReport.stock_report_id
            INNER JOIN Call
            ON StockSegment.start_call = Call.call_id
        ) CallStock
    )
    SELECT call_stock_data.start_call, ARRAY_AGG(call_stock_data.stock_data)
    FROM call_stock_data
    GROUP BY call_stock_data.start_call;
END;
$$;

CREATE TYPE OutLegCallData AS (
    arr_call_id INTEGER,
    arr_service_id TEXT,
    arr_service_run_date TIMESTAMP WITH TIME ZONE,
    plan_arr TIMESTAMP WITH TIME ZONE,
    act_arr TIMESTAMP WITH TIME ZONE,
    dep_call_id INTEGER,
    dep_service_id TEXT,
    dep_service_run_date TIMESTAMP WITH TIME ZONE,
    plan_dep TIMESTAMP WITH TIME ZONE,
    act_dep TIMESTAMP WITH TIME ZONE,
    station_crs CHARACTER(3),
    station_name TEXT,
    platform TEXT,
    mileage DECIMAL,
    stocks OutStockData[],
    assocs OutServiceAssocData[]
);

CREATE OR REPLACE FUNCTION GetLegCalls()
RETURNS TABLE (leg_id INTEGER, leg_calls OutLegCallData[])
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH LegCallData AS (
        SELECT
            LegCall.leg_id, (
                LegCall.arr_call_id,
                ArrCall.service_id,
                ArrCall.run_date,
                ArrCall.plan_arr,
                ArrCall.act_arr,
                LegCall.dep_call_id,
                DepCall.service_id,
                DepCall.run_date,
                DepCall.plan_dep,
                DepCall.act_dep,
                COALESCE(ArrCall.station_crs, DepCall.station_crs),
                COALESCE(ArrStation.station_name, DepStation.station_name),
                COALESCE(ArrCall.platform, DepCall.platform),
                LegCall.mileage,
                StockDetails.stock_info,
                CallAssocs.call_assocs
            )::OutLegCallData AS legcall_data
        FROM LegCall
        LEFT JOIN Call ArrCall
        ON LegCall.arr_call_id = ArrCall.call_id
        LEFT JOIN Station ArrStation
        ON ArrCall.station_crs = ArrStation.station_crs
        LEFT JOIN Call DepCall
        ON LegCall.dep_call_id = DepCall.call_id
        LEFT JOIN Station DepStation
        ON DepCall.station_crs = DepStation.station_crs
        LEFT JOIN (SELECT * FROM GetCallStockInfo()) StockDetails
        ON LegCall.dep_call_id = StockDetails.start_call
        LEFT JOIN (SELECT * FROM GetCallAssocData()) CallAssocs
        ON ArrCall.call_id = CallAssocs.call_id
        ORDER BY COALESCE(ArrCall.plan_arr, ArrCall.act_arr, DepCall.plan_dep, DepCall.act_arr) ASC
    )
    SELECT LegCallData.leg_id, ARRAY_AGG(LegCallData.legcall_data) AS leg_calls
    FROM LegCallData
    GROUP BY LegCallData.leg_id;
END;
$$;

CREATE TYPE OutLegStockSegmentData AS (
    segment_start OutServiceStationData,
    segment_end OutServiceStationData,
    segment_mileage DECIMAL,
    segment_stock OutLegStockData[]
);

CREATE TYPE OutLegData AS (
    leg_id INTEGER,
    leg_start TIMESTAMP WITH TIME ZONE,
    leg_services OutServiceData[],
    leg_calls OutLegCallData[],
    leg_stocks OutLegStockSegmentData[],
    leg_distance DECIMAL,
    leg_duration INTERVAL
);


CREATE OR REPLACE FUNCTION GetLegs(
    p_start_date TIMESTAMP WITH TIME ZONE,
    p_end_date TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF OutLegData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY SELECT
        Leg.leg_id AS leg_id,
        COALESCE(
            legcalls[0].plan_dep,
            legcalls[0].act_dep,
            legcalls[0].plan_arr,
            legcalls[0].act_arr
        )::TIMESTAMP WITH TIME ZONE AS leg_start,
        services AS leg_services,
        legcalls AS leg_calls,
        stocks AS leg_stocks,
        Leg.distance AS leg_distance,
        COALESCE(legcalls[-1].act_arr, legcalls[-1].plan_arr)::TIMESTAMP WITH TIME ZONE
        -
        COALESCE(legcalls[0].act_dep, legcalls[0].plan_dep)::TIMESTAMP WITH TIME ZONE
        AS leg_duration
    FROM Leg
    INNER JOIN (SELECT * FROM GetLegCalls()) legcall_table
    ON legcall_table.leg_id = leg.leg_id
    INNER JOIN (
        SELECT
            LegService.leg_id,
            JSON_AGG(service_details ORDER BY service_start ASC) AS services
        FROM (
            SELECT DISTINCT leg.leg_id, service.service_id
            FROM Leg
            INNER JOIN Legcall
            ON leg.leg_id = legcall.leg_id
            INNER JOIN call
            ON (
                Call.call_id = LegCall.arr_call_id
                OR Call.call_id = LegCall.dep_call_id
            )
            INNER JOIN service
            ON call.service_id = service.service_id
            AND call.run_date = service.run_date
        ) LegService
        INNER JOIN (
            WITH service_info AS (
                SELECT
                    Service.service_id, Service.run_date, headcode, origins,
                    destinations, calls, Operator.operator_id,
                    Operator.operator_code, Operator.operator_name,
                    Operator.bg_colour AS operator_bg,
                    Operator.fg_colour AS operator_fg, Brand.brand_id,
                    Brand.brand_code, Brand.brand_name,
                    Brand.bg_colour AS brand_bg, Brand.fg_colour AS brand_fg,
                    power,
                    COALESCE(calls[0].plan_arr, calls[0].act_arr, calls[0].plan_dep, calls[0].act_dep) AS service_start
                FROM Service
                INNER JOIN (
                    WITH endpoint_info AS (
                        SELECT service_id, run_date, Station.station_name, Station.station_crs
                        FROM ServiceEndpoint
                        INNER JOIN Station
                        ON ServiceEndpoint.station_crs = Station.station_crs
                        WHERE origin = true
                    )
                    SELECT
                        endpoint_info.service_id, endpoint_info.run_date,
                        JSON_AGG(endpoint_info.*) AS origins
                    FROM endpoint_info
                    GROUP BY (endpoint_info.service_id, endpoint_info.run_date)) origin_details
                On origin_details.service_id = Service.service_id
                AND origin_details.run_date = Service.run_date
                INNER JOIN (
                    WITH endpoint_info AS (
                        SELECT service_id, run_date, Station.station_name, Station.station_crs
                        FROM ServiceEndpoint
                        INNER JOIN Station
                        ON ServiceEndpoint.station_crs = Station.station_crs
                        WHERE origin = false
                    )
                    SELECT
                        endpoint_info.service_id, endpoint_info.run_date,
                        ARRAY_AGG(endpoint_info.*) AS destinations
                    FROM endpoint_info
                    GROUP BY (endpoint_info.service_id, endpoint_info.run_date)
                ) destination_details
                On destination_details.service_id = Service.service_id
                AND destination_details.run_date = Service.run_date
                INNER JOIN (
                    WITH call_info AS (
                        SELECT
                            Call.call_id, service_id, run_date, station_name, Call.station_crs,
                            platform, plan_arr, plan_dep, act_arr, act_dep,
                            mileage, associations
                        FROM Call
                        INNER JOIN Station
                        ON Call.station_crs = Station.station_crs
                        LEFT JOIN (
                            WITH AssociationInfo AS (
                                SELECT
                                    call_id, associated_id,
                                    associated_run_date, associated_type
                                FROM AssociatedService
                            )
                            SELECT
                                call_id,
                                ARRAY_AGG(AssociationInfo.*) AS associations
                            FROM AssociationInfo
                            GROUP BY call_id
                        ) Association
                        ON Call.call_id = Association.call_id
                        ORDER BY COALESCE(plan_arr, act_arr, plan_dep, act_dep) ASC
                    )
                    SELECT service_id, run_date, ARRAY_AGG(call_info.*) AS calls
                    FROM call_info
                    GROUP BY (service_id, run_date)
                ) call_details
                ON Service.service_id = call_details.service_id
                INNER JOIN Operator
                ON Service.operator_id = Operator.operator_id
                LEFT JOIN Brand
                ON Service.brand_id = Brand.brand_id
                ORDER BY service_start ASC
            )
            SELECT
                service_id, run_date, service_start,
                ARRAY_AGG(service_info.*) AS service_details
            FROM service_info
            GROUP BY (service_id, run_date, service_start)
            ORDER BY service_start ASC
        ) ServiceDetails
        ON ServiceDetails.service_id = LegService.service_id
        GROUP BY LegService.leg_id
    ) LegServices
    ON LegServices.leg_id = Leg.leg_id
    INNER JOIN (
        WITH StockSegment AS (
            WITH StockSegmentDetail AS (
                WITH StockDetail AS (
                    SELECT
                        stock_class, stock_subclass, stock_number,
                        stock_cars, start_call, end_call
                    FROM StockReport
                    INNER JOIN StockSegmentReport
                    ON StockReport.stock_report_id = StockSegmentReport.stock_report_id
                    INNER JOIN StockSegment
                    ON StockSegmentReport.stock_segment_id = StockSegment.stock_segment_id
                )
                SELECT
                    start_call, end_call, ARRAY_AGG(StockDetail.*) AS stocks
                FROM StockDetail
                GROUP BY start_call, end_call
            )
            SELECT
                StartLegCall.leg_id,
                COALESCE(StartCall.plan_dep, StartCall.plan_arr, StartCall.act_dep, StartCall.act_arr) AS segment_start,
                StartStation.station_crs AS start_crs,
                StartStation.station_name AS start_name,
                EndStation.station_crs AS end_crs,
                EndStation.station_name AS end_name,
                Service.service_id, Service.run_date,
                EndLegCall.mileage - StartLegCall.mileage AS distance,
                COALESCE(EndCall.act_arr, EndCall.plan_arr) -
                COALESCE(StartCall.act_dep, StartCall.plan_dep) AS duration,
                ARRAY_AGG(StockSegmentDetail.*) AS stocks
            FROM StockSegmentDetail
            INNER JOIN Call StartCall
            ON StockSegmentDetail.start_call = StartCall.call_id
            INNER JOIN Station StartStation
            ON StartCall.station_crs = StartStation.station_crs
            INNER JOIN Call EndCall
            ON StockSegmentDetail.end_call = EndCall.call_id
            INNER JOIN Station EndStation
            ON EndCall.station_crs = EndStation.station_crs
            INNER JOIN LegCall StartLegCall
            ON StartLegCall.dep_call_id = StartCall.call_id
            INNER JOIN LegCall EndLegCall
            ON EndLegCall.arr_call_id = EndCall.call_id
            INNER JOIN Service
            ON StartCall.service_id = Service.service_id
            AND StartCall.run_date = Service.run_date
            GROUP BY
                StartLegCall.leg_id, segment_start, start_crs, start_name,
                end_crs, end_name, Service.service_id, Service.run_date,
                distance, duration
        )
        SELECT stocksegment.leg_id, ARRAY_AGG(StockSegment.* ORDER BY segment_start ASC) AS stocks
        FROM StockSegment
        GROUP BY stocksegment.leg_id
    ) StockDetails
    ON StockDetails.leg_id = Leg.leg_id;
END;
$$;
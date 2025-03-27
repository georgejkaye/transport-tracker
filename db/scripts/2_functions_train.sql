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

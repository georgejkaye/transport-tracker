CREATE OR REPLACE FUNCTION SelectCallAssocData()
RETURNS TABLE (call_id INTEGER, call_assocs OutAssocData[])
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH assocs AS (
        SELECT
            AssocData.call_id,
            (associated_id, associated_run_date, associated_type)::OutAssocData AS call_assocs
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

CREATE OR REPLACE FUNCTION SelectCallStockInfo()
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

CREATE OR REPLACE FUNCTION SelectLegCalls()
RETURNS TABLE (leg_id INTEGER, leg_calls OutLegCallData[])
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        LegCallData.leg_id,
        ARRAY_AGG(
            LegCallData.legcall_data
            ORDER BY COALESCE(
                (LegCallData.legcall_data).plan_arr,
                (LegCallData.legcall_data).plan_dep,
                (LegCallData.legcall_data).act_arr,
                (LegCallData.legcall_data).act_dep
            )
        ) AS leg_calls
    FROM (
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
                (
                    COALESCE(ArrCall.station_crs, DepCall.station_crs),
                    COALESCE(ArrStation.station_name, DepStation.station_name)
                )::OutStationData,
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
        LEFT JOIN (SELECT * FROM SelectCallStockInfo()) StockDetails
        ON LegCall.dep_call_id = StockDetails.start_call
        LEFT JOIN (SELECT * FROM SelectCallAssocData()) CallAssocs
        ON ArrCall.call_id = CallAssocs.call_id
        ORDER BY COALESCE(ArrCall.plan_arr, ArrCall.act_arr, DepCall.plan_dep, DepCall.act_arr) ASC
    ) LegCallData
    GROUP BY LegCallData.leg_id;
END;
$$;

CREATE OR REPLACE FUNCTION SelectServiceEndpoints(
    p_origin BOOLEAN
)
RETURNS TABLE (
    service_id TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    endpoint_data OutStationData[])
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH EndpointData AS (
        SELECT
            ServiceEndpoint.service_id,
            ServiceEndpoint.run_date,
            (Station.station_crs, Station.station_name)::OutStationData AS endpoint_data
        FROM ServiceEndpoint
        INNER JOIN Station
        ON ServiceEndpoint.station_crs = Station.station_crs
        WHERE origin = p_origin
    )
    SELECT
        EndpointData.service_id,
        EndpointData.run_date,
        ARRAY_AGG(EndpointData.endpoint_data) AS endpoint_data
    FROM EndpointData
    GROUP BY (EndpointData.service_id, EndpointData.run_date);
END;
$$;

CREATE OR REPLACE FUNCTION SelectServiceCalls()
RETURNS TABLE (
    service_id TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    call_data OutCallData[]
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH CallInfo AS (
        SELECT
            Call.service_id,
            Call.run_date, (
                (
                    Call.station_crs,
                    Station.station_name
                )::OutStationData,
                Call.platform,
                Call.plan_arr,
                Call.plan_dep,
                Call.act_arr,
                Call.act_dep,
                CallAssoc.call_assocs,
                Call.mileage
            )::OutCallData AS call_data
        FROM Call
        INNER JOIN Station
        ON Call.station_crs = Station.station_crs
        LEFT JOIN (SELECT * FROM SelectCallAssocData()) CallAssoc
        ON CallAssoc.call_id = Call.call_id
        ORDER BY COALESCE(Call.plan_arr, Call.plan_dep, Call.act_arr, Call.act_dep)
    )
    SELECT
        CallInfo.service_id,
        CallInfo.run_date,
        ARRAY_AGG(CallInfo.call_data) AS call_data
    FROM CallInfo
    GROUP BY (CallInfo.service_id, CallInfo.run_date);
END;
$$;

CREATE OR REPLACE FUNCTION SelectServiceAssocs()
RETURNS TABLE (
    service_id TEXT,
    service_run_date TIMESTAMP WITH TIME ZONE,
    service_assocs OutServiceAssocData[]
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH ServiceAssoc AS (
        SELECT
            Call.service_id,
            Call.run_date,
            (
                AssociatedService.call_id,
                AssociatedService.associated_id,
                AssociatedService.associated_run_date,
                AssociatedService.associated_type
            )::OutServiceAssocData AS service_assoc
        FROM AssociatedService
        INNER JOIN Call
        On AssociatedService.call_id = Call.call_id
    )
    SELECT
        ServiceAssoc.service_id,
        ServiceAssoc.run_date AS service_run_date,
        ARRAY_AGG(ServiceAssoc.service_assoc) AS service_assocs
    FROM ServiceAssoc
    GROUP BY (ServiceAssoc.service_id, ServiceAssoc.run_date);
END;
$$;

CREATE OR REPLACE FUNCTION SelectLegServiceIds()
RETURNS TABLE (leg_id INTEGER, service_id TEXT, run_date TIMESTAMP WITH TIME ZONE)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT DISTINCT Leg.leg_id, Service.service_id, Service.run_date
    FROM Leg
    INNER JOIN Legcall
    ON Leg.leg_id = LegCall.leg_id
    INNER JOIN call
    ON (
        Call.call_id = LegCall.arr_call_id
        OR Call.call_id = LegCall.dep_call_id
    )
    INNER JOIN service
    ON Call.service_id = Service.service_id
    AND Call.run_date = Service.run_date;
END;
$$;

CREATE OR REPLACE FUNCTION SelectServiceData()
RETURNS TABLE (
    service_id TEXT,
    service_run_date TIMESTAMP WITH TIME ZONE,
    service_data OutServiceData
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        Service.service_id,
        Service.run_date,
        (
            Service.service_id,
            Service.run_date,
            Service.headcode,
            COALESCE(
                ServiceCall.call_data[1].plan_arr,
                ServiceCall.call_data[1].act_arr,
                ServiceCall.call_data[1].plan_dep,
                ServiceCall.call_data[1].act_dep
            ),
            ServiceOrigin.endpoint_data,
            ServiceDestination.endpoint_data,
            (
                Operator.operator_id,
                Operator.operator_code,
                Operator.operator_name,
                Operator.bg_colour,
                Operator.fg_colour
            )::OutOperatorData,
            (
                Brand.brand_id,
                Brand.brand_code,
                Brand.brand_name,
                Brand.bg_colour,
                Brand.fg_colour
            )::OutBrandData,
            ServiceCall.call_data,
            ServiceAssoc.service_assocs
        )::OutServiceData AS service_data
    FROM Service
    LEFT JOIN (SELECT * FROM SelectServiceEndpoints(true)) ServiceOrigin
    On ServiceOrigin.service_id = Service.service_id
    AND ServiceOrigin.run_date = Service.run_date
    LEFT JOIN (SELECT * FROM SelectServiceEndpoints(false)) ServiceDestination
    On ServiceDestination.service_id = Service.service_id
    AND ServiceDestination.run_date = Service.run_date
    LEFT JOIN (SELECT * FROM SelectServiceCalls()) ServiceCall
    ON Service.service_id = ServiceCall.service_id
    AND Service.run_date = ServiceCall.run_date
    LEFT JOIN (SELECT * FROM SelectServiceAssocs()) ServiceAssoc
    ON Service.service_id = ServiceAssoc.service_id
    AND Service.run_date = ServiceAssoc.service_run_date
    INNER JOIN Operator
    ON Service.operator_id = Operator.operator_id
    LEFT JOIN Brand
    ON Service.brand_id = Brand.brand_id
    ORDER BY (service_data).service_start;
END;
$$;

CREATE OR REPLACE FUNCTION SelectLegServices()
RETURNS TABLE (leg_id INTEGER, leg_services OutServiceData[])
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        LegServiceId.leg_id,
        ARRAY_AGG(ServiceData.service_data) AS services
    FROM (SELECT * FROM SelectLegServiceIds()) LegServiceId
    INNER JOIN (SELECT * FROM SelectServiceData()) ServiceData
    ON ServiceData.service_id = LegServiceId.service_id
    AND ServiceData.service_run_date = LegServiceId.run_date
    GROUP BY LegServiceId.leg_id;
END;
$$;

CREATE OR REPLACE FUNCTION SelectStockSegmentStockReports()
RETURNS TABLE (stock_segment_id INTEGER, stock_data OutStockData[])
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        StockSegment.stock_segment_id,
        ARRAY_AGG(StockReportData.stock_report)
    FROM StockSegment
    INNER JOIN StockSegmentReport
    ON StockSegmentReport.stock_segment_id = StockSegment.stock_segment_id
    INNER JOIN (
        SELECT stock_report_id, (
            stock_class,
            stock_subclass,
            stock_number,
            stock_cars
        )::OutStockData AS stock_report
        FROM StockReport
    ) StockReportData
    ON StockReportData.stock_report_id = StockSegmentReport.stock_report_id
    GROUP BY StockSegment.stock_segment_id;
END;
$$;

CREATE OR REPLACE FUNCTION SelectLegStock()
RETURNS TABLE (leg_id INTEGER, leg_stock OutLegStock[])
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        LegStockSegment.leg_id,
        ARRAY_AGG(
            LegStockSegment.stock_segment
            ORDER BY (LegStockSegment.stock_segment).segment_start
        ) AS leg_stock
    FROM (
        SELECT
            StartLegCall.leg_id,
            (
                COALESCE(
                    StartCall.plan_dep,
                    StartCall.plan_arr,
                    StartCall.act_dep,
                    StartCall.act_arr
                ), (
                    StartStation.station_crs,
                    StartStation.station_name
                )::OutStationData,
                (
                    EndStation.station_crs,
                    EndStation.station_name
                )::OutStationData,
                EndLegCall.mileage - StartLegCall.mileage,
                COALESCE(EndCall.act_arr, EndCall.plan_arr) -
                COALESCE(StartCall.act_dep, StartCall.plan_dep),
                StockSegmentStockReport.stock_data
            )::OutLegStock AS stock_segment
        FROM StockSegment
        INNER JOIN (SELECT * FROM SelectStockSegmentStockReports()) StockSegmentStockReport
        ON StockSegment.stock_segment_id = StockSegmentStockReport.stock_segment_id
        INNER JOIN Call StartCall
        ON StockSegment.start_call = StartCall.call_id
        INNER JOIN Station StartStation
        ON StartCall.station_crs = StartStation.station_crs
        INNER JOIN Call EndCall
        ON StockSegment.end_call = EndCall.call_id
        INNER JOIN Station EndStation
        ON EndCall.station_crs = EndStation.station_crs
        INNER JOIN LegCall StartLegCall
        ON StartLegCall.dep_call_id = StartCall.call_id
        INNER JOIN LegCall EndLegCall
        ON EndLegCall.arr_call_id = EndCall.call_id
    ) LegStockSegment
    GROUP BY LegStockSegment.leg_id;
END;
$$;

CREATE OR REPLACE FUNCTION SelectLegs(
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS SETOF OutLegData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY SELECT
        LegDetails.leg_id,
        LegDetails.leg_start,
        LegDetails.leg_services,
        LegDetails.leg_calls,
        LegDetails.leg_stock,
        LegDetails.leg_distance,
        LegDetails.leg_end - LegDetails.leg_start AS leg_duration
    FROM (
        SELECT
            Leg.leg_id AS leg_id,
            COALESCE(
                LegCallLink.leg_calls[1].plan_dep,
                LegCallLink.leg_calls[1].act_dep,
                LegCallLink.leg_calls[1].plan_arr,
                LegCallLink.leg_calls[1].act_arr
            ) AS leg_start,
            COALESCE(
                LegCallLink.leg_calls[ARRAY_LENGTH(LegCallLink.leg_calls, 1)].act_arr,
                LegCallLink.leg_calls[ARRAY_LENGTH(LegCallLink.leg_calls, 1)].plan_arr,
                LegCallLink.leg_calls[ARRAY_LENGTH(LegCallLink.leg_calls, 1)].act_dep,
                LegCallLink.leg_calls[ARRAY_LENGTH(LegCallLink.leg_calls, 1)].plan_dep
            ) AS leg_end,
            LegService.leg_services,
            LegCallLink.leg_calls,
            LegStock.leg_stock,
            Leg.distance AS leg_distance
        FROM Leg
        INNER JOIN (SELECT * FROM SelectLegServices()) LegService
        ON LegService.leg_id = Leg.leg_id
        INNER JOIN (SELECT * FROM SelectLegCalls()) LegCallLink
        ON LegCallLink.leg_id = Leg.leg_id
        INNER JOIN (SELECT * FROM SelectLegStock()) LegStock
        ON LegStock.leg_id = Leg.leg_id
    ) LegDetails
    WHERE (p_start_date IS NULL OR LegDetails.leg_start >= p_start_date)
    AND (p_end_date IS NULL OR LegDetails.leg_start <= p_end_date)
    ORDER BY LegDetails.leg_start DESC;
END;
$$;
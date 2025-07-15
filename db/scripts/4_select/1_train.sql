CREATE OR REPLACE FUNCTION SelectCallAssocData()
RETURNS TABLE (call_id INTEGER, call_assocs TrainAssociatedService[])
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH assocs AS (
        SELECT
            AssocData.train_call_id,
            (associated_id, associated_run_date, associated_type)::TrainAssociatedService AS call_assocs
        FROM (
            SELECT
                TrainAssociatedService.train_call_id,
                TrainAssociatedService.associated_id,
                TrainAssociatedService.associated_run_date,
                TrainAssociatedService.associated_type
            FROM TrainAssociatedService
        ) AssocData
    )
    SELECT
        assocs.train_call_id,
        ARRAY_AGG(assocs.call_assocs) AS associations
    FROM assocs
    GROUP BY assocs.train_call_id;
END;
$$;

CREATE OR REPLACE FUNCTION SelectCallStockInfo()
RETURNS TABLE (start_call INTEGER, stock_info TrainStockOutData[])
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH call_stock_data AS (
        SELECT
            CallStock.start_call,
            (stock_class, stock_subclass, stock_number, stock_cars)::TrainStockOutData AS stock_data
        FROM (
            SELECT TrainStockSegment.start_call, stock_class, stock_subclass,
                stock_number, stock_cars
            FROM TrainStockSegment
            INNER JOIN TrainStockSegmentReport
            ON TrainStockSegment.stock_segment_id = TrainStockSegmentReport.stock_segment_id
            INNER JOIN TrainStockReport
            ON TrainStockSegmentReport.stock_report_id = TrainStockReport.stock_report_id
            INNER JOIN TrainCall
            ON TrainStockSegment.start_call = TrainCall.train_call_id
        ) CallStock
    )
    SELECT call_stock_data.start_call, ARRAY_AGG(call_stock_data.stock_data)
    FROM call_stock_data
    GROUP BY call_stock_data.start_call;
END;
$$;

CREATE OR REPLACE FUNCTION SelectLegCalls()
RETURNS TABLE (leg_id INTEGER, leg_calls TrainLegCallOutData[])
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        LegCallData.train_leg_id,
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
            TrainLegCall.train_leg_id, (
                TrainLegCall.arr_call_id,
                ArrCall.train_service_id,
                ArrCall.run_date,
                ArrCall.plan_arr,
                ArrCall.act_arr,
                TrainLegCall.dep_call_id,
                DepCall.train_service_id,
                DepCall.run_date,
                DepCall.plan_dep,
                DepCall.act_dep,
                (
                    COALESCE(ArrCall.station_crs, DepCall.station_crs),
                    COALESCE(ArrStation.station_name, DepStation.station_name)
                )::TrainStationOutData,
                COALESCE(ArrCall.platform, DepCall.platform),
                TrainLegCall.mileage,
                StockDetails.stock_info,
                CallAssocs.call_assocs
            )::TrainLegCallOutData AS legcall_data
        FROM TrainLegCall
        LEFT JOIN TrainCall ArrCall
        ON TrainLegCall.arr_call_id = ArrCall.train_call_id
        LEFT JOIN TrainStation ArrStation
        ON ArrCall.station_crs = ArrStation.station_crs
        LEFT JOIN TrainCall DepCall
        ON TrainLegCall.dep_call_id = DepCall.train_call_id
        LEFT JOIN TrainStation DepStation
        ON DepCall.station_crs = DepStation.station_crs
        LEFT JOIN (SELECT * FROM SelectCallStockInfo()) StockDetails
        ON TrainLegCall.dep_call_id = StockDetails.start_call
        LEFT JOIN (SELECT * FROM SelectCallAssocData()) CallAssocs
        ON ArrCall.train_call_id = CallAssocs.train_call_id
        ORDER BY COALESCE(ArrCall.plan_arr, ArrCall.act_arr, DepCall.plan_dep, DepCall.act_arr) ASC
    ) LegCallData
    GROUP BY LegCallData.train_leg_id;
END;
$$;

CREATE OR REPLACE FUNCTION SelectServiceEndpoints(
    p_origin BOOLEAN
)
RETURNS TABLE (
    service_id TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    endpoint_data TrainStationOutData[])
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH EndpointData AS (
        SELECT
            TrainServiceEndpoint.train_service_id,
            TrainServiceEndpoint.run_date,
            (TrainStation.station_crs, TrainStation.station_name)::TrainStationOutData AS endpoint_data
        FROM TrainServiceEndpoint
        INNER JOIN TrainStation
        ON TrainServiceEndpoint.station_crs = TrainStation.station_crs
        WHERE origin = p_origin
    )
    SELECT
        EndpointData.train_service_id,
        EndpointData.run_date,
        ARRAY_AGG(EndpointData.endpoint_data) AS endpoint_data
    FROM EndpointData
    GROUP BY (EndpointData.train_service_id, EndpointData.run_date);
END;
$$;

CREATE OR REPLACE FUNCTION SelectServiceCalls()
RETURNS TABLE (
    service_id TEXT,
    run_date TIMESTAMP WITH TIME ZONE,
    call_data TrainCallOutData[]
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH CallInfo AS (
        SELECT
            TrainCall.train_service_id,
            TrainCall.run_date, (
                (
                    TrainCall.station_crs,
                    TrainStation.station_name
                )::TrainStationOutData,
                TrainCall.platform,
                TrainCall.plan_arr,
                TrainCall.plan_dep,
                TrainCall.act_arr,
                TrainCall.act_dep,
                CallAssoc.call_assocs,
                TrainCall.mileage
            )::TrainCallOutData AS call_data
        FROM TrainCall
        INNER JOIN TrainStation
        ON TrainCall.station_crs = TrainStation.station_crs
        LEFT JOIN (SELECT * FROM SelectCallAssocData()) CallAssoc
        ON CallAssoc.train_call_id = TrainCall.train_call_id
        ORDER BY COALESCE(TrainCall.plan_arr, TrainCall.plan_dep, TrainCall.act_arr, TrainCall.act_dep)
    )
    SELECT
        CallInfo.train_service_id,
        CallInfo.run_date,
        ARRAY_AGG(CallInfo.call_data) AS call_data
    FROM CallInfo
    GROUP BY (CallInfo.train_service_id, CallInfo.run_date);
END;
$$;

CREATE OR REPLACE FUNCTION SelectServiceAssocs()
RETURNS TABLE (
    service_id TEXT,
    service_run_date TIMESTAMP WITH TIME ZONE,
    service_assocs TrainAssociatedServiceOutData[]
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH ServiceAssoc AS (
        SELECT
            TrainCall.train_service_id,
            TrainCall.run_date,
            (
                TrainAssociatedService.train_call_id,
                TrainAssociatedService.associated_id,
                TrainAssociatedService.associated_run_date,
                TrainAssociatedService.associated_type
            )::TrainAssociatedServiceOutData AS service_assoc
        FROM TrainAssociatedService
        INNER JOIN TrainCall
        On TrainAssociatedService.train_call_id = TrainCall.train_call_id
    )
    SELECT
        ServiceAssoc.train_service_id,
        ServiceAssoc.run_date AS service_run_date,
        ARRAY_AGG(ServiceAssoc.service_assoc) AS service_assocs
    FROM ServiceAssoc
    GROUP BY (ServiceAssoc.train_service_id, ServiceAssoc.run_date);
END;
$$;

CREATE OR REPLACE FUNCTION SelectLegServiceIds()
RETURNS TABLE (leg_id INTEGER, service_id TEXT, run_date TIMESTAMP WITH TIME ZONE)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT DISTINCT TrainLeg.train_leg_id, TrainService.train_service_id, TrainService.run_date
    FROM TrainLeg
    INNER JOIN Legcall
    ON TrainLeg.train_leg_id = TrainLegCall.train_leg_id
    INNER JOIN call
    ON (
        TrainCall.train_call_id = TrainLegCall.arr_call_id
        OR TrainCall.train_call_id = TrainLegCall.dep_call_id
    )
    INNER JOIN service
    ON TrainCall.train_service_id = TrainService.train_service_id
    AND TrainCall.run_date = TrainService.run_date;
END;
$$;

CREATE OR REPLACE FUNCTION SelectServiceData()
RETURNS TABLE (
    service_id TEXT,
    service_run_date TIMESTAMP WITH TIME ZONE,
    service_data TrainServiceOutData
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        TrainService.train_service_id,
        TrainService.run_date,
        (
            TrainService.train_service_id,
            TrainService.run_date,
            TrainService.headcode,
            COALESCE(
                ServiceCall.call_data[1].plan_arr,
                ServiceCall.call_data[1].act_arr,
                ServiceCall.call_data[1].plan_dep,
                ServiceCall.call_data[1].act_dep
            ),
            ServiceOrigin.endpoint_data,
            ServiceDestination.endpoint_data,
            (
                TrainOperator.train_operator_id,
                TrainOperator.operator_code,
                TrainOperator.operator_name,
                TrainOperator.bg_colour,
                TrainOperator.fg_colour
            )::TrainOperatorOutData,
            (
                TrainBrand.train_brand_id,
                TrainBrand.brand_code,
                TrainBrand.brand_name,
                TrainBrand.bg_colour,
                TrainBrand.fg_colour
            )::TrainBrandOutData,
            ServiceCall.call_data,
            ServiceAssoc.service_assocs
        )::TrainServiceOutData AS service_data
    FROM TrainService
    LEFT JOIN (SELECT * FROM SelectServiceEndpoints(true)) ServiceOrigin
    On ServiceOrigin.train_service_id = TrainService.train_service_id
    AND ServiceOrigin.run_date = TrainService.run_date
    LEFT JOIN (SELECT * FROM SelectServiceEndpoints(false)) ServiceDestination
    On ServiceDestination.train_service_id = TrainService.train_service_id
    AND ServiceDestination.run_date = TrainService.run_date
    LEFT JOIN (SELECT * FROM SelectServiceCalls()) ServiceCall
    ON TrainService.train_service_id = ServiceCall.train_service_id
    AND TrainService.run_date = ServiceCall.run_date
    LEFT JOIN (SELECT * FROM SelectServiceAssocs()) ServiceAssoc
    ON TrainService.train_service_id = ServiceAssoc.train_service_id
    AND TrainService.run_date = ServiceAssoc.service_run_date
    INNER JOIN TrainOperator
    ON TrainService.train_operator_id = TrainOperator.train_operator_id
    LEFT JOIN TrainBrand
    ON TrainService.train_brand_id = TrainBrand.train_brand_id
    ORDER BY (service_data).service_start;
END;
$$;

CREATE OR REPLACE FUNCTION SelectLegServices()
RETURNS TABLE (leg_id INTEGER, leg_services TrainServiceOutData[])
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        LegServiceId.train_leg_id,
        ARRAY_AGG(ServiceData.service_data) AS services
    FROM (SELECT * FROM SelectLegServiceIds()) LegServiceId
    INNER JOIN (SELECT * FROM SelectServiceData()) ServiceData
    ON ServiceData.train_service_id = LegServiceId.train_service_id
    AND ServiceData.service_run_date = LegServiceId.run_date
    GROUP BY LegServiceId.train_leg_id;
END;
$$;

CREATE OR REPLACE FUNCTION SelectStockSegmentStockReports()
RETURNS TABLE (stock_segment_id INTEGER, stock_data TrainStockOutData[])
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        TrainStockSegment.stock_segment_id,
        ARRAY_AGG(StockReportData.stock_report)
    FROM TrainStockSegment
    INNER JOIN TrainStockSegmentReport
    ON TrainStockSegmentReport.stock_segment_id = TrainStockSegment.stock_segment_id
    INNER JOIN (
        SELECT stock_report_id, (
            stock_class,
            stock_subclass,
            stock_number,
            stock_cars
        )::TrainStockOutData AS stock_report
        FROM TrainStockReport
    ) StockReportData
    ON StockReportData.stock_report_id = TrainStockSegmentReport.stock_report_id
    GROUP BY TrainStockSegment.stock_segment_id;
END;
$$;

CREATE OR REPLACE FUNCTION SelectLegStock()
RETURNS TABLE (leg_id INTEGER, leg_stock TrainLegStockOutData[])
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        LegStockSegment.train_leg_id,
        ARRAY_AGG(
            LegStockSegment.stock_segment
            ORDER BY (LegStockSegment.stock_segment).segment_start
        ) AS leg_stock
    FROM (
        SELECT
            StartLegCall.train_leg_id,
            (
                COALESCE(
                    StartCall.plan_dep,
                    StartCall.plan_arr,
                    StartCall.act_dep,
                    StartCall.act_arr
                ), (
                    StartStation.station_crs,
                    StartStation.station_name
                )::TrainStationOutData,
                (
                    EndStation.station_crs,
                    EndStation.station_name
                )::TrainStationOutData,
                EndLegCall.mileage - StartLegCall.mileage,
                COALESCE(EndCall.act_arr, EndCall.plan_arr) -
                COALESCE(StartCall.act_dep, StartCall.plan_dep),
                StockSegmentStockReport.stock_data
            )::TrainLegStockOutData AS stock_segment
        FROM TrainStockSegment
        INNER JOIN (SELECT * FROM SelectStockSegmentStockReports()) StockSegmentStockReport
        ON TrainStockSegment.stock_segment_id = StockSegmentStockReport.stock_segment_id
        INNER JOIN TrainCall StartCall
        ON TrainStockSegment.start_call = StartCall.train_call_id
        INNER JOIN TrainStation StartStation
        ON StartCall.station_crs = StartStation.station_crs
        INNER JOIN TrainCall EndCall
        ON TrainStockSegment.end_call = EndCall.train_call_id
        INNER JOIN TrainStation EndStation
        ON EndCall.station_crs = EndStation.station_crs
        INNER JOIN TrainLegCall StartLegCall
        ON StartLegCall.dep_call_id = StartCall.train_call_id
        INNER JOIN TrainLegCall EndLegCall
        ON EndLegCall.arr_call_id = EndCall.train_call_id
    ) LegStockSegment
    GROUP BY LegStockSegment.train_leg_id;
END;
$$;

CREATE OR REPLACE FUNCTION SelectLegs(
    p_user_id INTEGER,
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_leg_id INTEGER DEFAULT NULL
)
RETURNS SETOF TrainLegOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY SELECT
        LegDetails.train_leg_id,
        LegDetails.user_id,
        LegDetails.leg_start,
        LegDetails.leg_services,
        LegDetails.leg_calls,
        LegDetails.leg_stock,
        LegDetails.leg_distance,
        LegDetails.leg_end - LegDetails.leg_start AS leg_duration
    FROM (
        SELECT
            TrainLeg.train_leg_id AS leg_id,
            TrainLeg.user_id AS user_id,
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
            TrainLeg.distance AS leg_distance
        FROM TrainLeg
        INNER JOIN (SELECT * FROM SelectLegServices()) LegService
        ON LegService.train_leg_id = TrainLeg.train_leg_id
        INNER JOIN (SELECT * FROM SelectLegCalls()) LegCallLink
        ON LegCallLink.train_leg_id = TrainLeg.train_leg_id
        INNER JOIN (SELECT * FROM SelectLegStock()) LegStock
        ON LegStock.train_leg_id = TrainLeg.train_leg_id
    ) LegDetails
    WHERE (p_start_date IS NULL OR LegDetails.leg_start >= p_start_date)
    AND (p_end_date IS NULL OR LegDetails.leg_start <= p_end_date)
    AND (p_leg_id IS NULL OR LegDetails.train_leg_id = p_leg_id)
    AND p_user_id = LegDetails.user_id
    ORDER BY LegDetails.leg_start DESC;
END;
$$;

CREATE OR REPLACE FUNCTION GetStationDetailsFromNames(
    p_station_names TEXT[]
)
RETURNS SETOF StationDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT station_crs, station_name, longitude, latitude
    FROM TrainStation
    WHERE station_name = ANY(p_station_names);
END;
$$;

CREATE OR REPLACE FUNCTION GetStationDetailsFromCrses(
    p_station_crses TEXT[]
)
RETURNS SETOF StationDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT station_crs, station_name, longitude, latitude
    FROM TrainStation
    WHERE station_crs = ANY(p_station_crses);
END;
$$;

CREATE OR REPLACE FUNCTION GetStationPoints(
    p_station_crs CHARACTER(3),
    p_platform TEXT
)
RETURNS SETOF StationLatLon
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT platform, latitude, longitude
    FROM TrainStationPoint
    WHERE station_crs = p_station_crs
    AND (p_platform IS NULL OR platform = p_platform);
END;
$$;

CREATE OR REPLACE FUNCTION GetStationPointsFromName(
    p_station_name TEXT,
    p_platform TEXT
)
RETURNS SETOF StationLatLon
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT platform, latitude, longitude
    FROM TrainStationPoint
    INNER JOIN TrainStation
    ON TrainStation.station_crs = TrainStationPoint.station_crs
    WHERE station_name = p_station_name
    AND (p_platform IS NULL OR platform = p_platform);
END;
$$;

CREATE OR REPLACE FUNCTION GetStationPointsFromCrses(
    p_stations StationCrsAndPlatform[]
)
RETURNS SETOF StationAndPoints
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT points.station_crs, station_name, ARRAY_AGG(station_point)
    FROM (
        WITH
            arr AS (SELECT * FROM unnest(p_stations)),
            platform_match AS (
                SELECT TrainStationPoint.*, station_name
                FROM TrainStationPoint
                INNER JOIN arr
                ON arr.station_crs = TrainStationPoint.station_crs
                AND arr.station_platform = TrainStationPoint.platform
                INNER JOIN TrainStation
                ON TrainStation.station_crs = TrainStationPoint.station_crs
            ),
            station_match AS (
                SELECT TrainStationPoint.*, station_name
                FROM TrainStationPoint
                INNER JOIN arr
                ON arr.station_crs = TrainStationPoint.station_crs
                INNER JOIN TrainStation
                ON TrainStation.station_crs = TrainStationPoint.station_crs
            )
        SELECT
            station_crs,
            station_name,
            (platform, latitude, longitude)::StationLatLon AS station_point
        FROM (
            SELECT *
            FROM platform_match
            UNION
            SELECT * FROM station_match
            WHERE station_match.station_crs
            NOT IN (
                SELECT platform_match.station_crs FROM platform_match
            )
        )
    ) points
    GROUP BY (station_crs, station_name);
END;
$$;

CREATE OR REPLACE FUNCTION GetStationPointsFromNames(
    p_stations StationNameAndPlatform[]
)
RETURNS SETOF StationNameAndPoints
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT points.station_crs, points.station_name, points.search_name, ARRAY_AGG(points.station_point)
    FROM (
        WITH
            arr AS (SELECT * FROM unnest(p_stations)),
            platform_match AS (
                SELECT
                    names.station_crs,
                    names.station_name,
                    names.platform,
                    latitude,
                    longitude
                FROM ((
                    SELECT TrainStationPoint.*, TrainStation.station_name
                    FROM TrainStationPoint
                    INNER JOIN TrainStation
                    ON TrainStationPoint.station_crs = TrainStation.station_crs
                ) UNION (
                    SELECT TrainStationPoint.*, TrainStationName.alternate_station_name AS station_name
                    FROM TrainStationPoint
                    INNER JOIN TrainStation
                    ON TrainStationPoint.station_crs = TrainStation.station_crs
                    INNER JOIN TrainStationName
                    ON TrainStationPoint.station_crs = TrainStationName.station_crs
                )) names
                INNER JOIN arr
                ON arr.station_name = names.station_name
                AND arr.station_platform = names.platform
            ),
            station_match AS (
                SELECT
                    names.station_crs,
                    names.station_name,
                    names.platform,
                    latitude,
                    longitude
                FROM ((
                    SELECT TrainStationPoint.*, TrainStation.station_name
                    FROM TrainStationPoint
                    INNER JOIN TrainStation
                    ON TrainStationPoint.station_crs = TrainStation.station_crs
                ) UNION (
                    SELECT TrainStationPoint.*, TrainStationName.alternate_station_name AS station_name
                    FROM TrainStationPoint
                    INNER JOIN TrainStation
                    ON TrainStationPoint.station_crs = TrainStation.station_crs
                    INNER JOIN TrainStationName
                    ON TrainStationPoint.station_crs = TrainStationName.station_crs
                )) names
                INNER JOIN arr
                ON arr.station_name = names.station_name
                WHERE station_crs
                NOT IN (
                    SELECT platform_match.station_crs FROM platform_match
                )
            )
        SELECT
            TrainStation.station_crs,
            TrainStation.station_name,
            Match.station_name AS search_name,
            (platform, latitude, longitude)::StationLatLon
            AS station_point
        FROM ((
            SELECT
                platform_match.station_crs,
                platform_match.station_name,
                platform_match.platform,
                platform_match.latitude,
                platform_match.longitude
            FROM platform_match
        ) UNION (
            SELECT
                station_match.station_crs,
                station_match.station_name,
                station_match.platform,
                station_match.latitude,
                station_match.longitude
            FROM station_match
        )) Match
        INNER JOIN TrainStation
        ON TrainStation.station_crs = Match.station_crs
    ) points
    GROUP BY (station_crs, station_name, search_name);
END;
$$;

CREATE OR REPLACE FUNCTION GetStationPoints()
RETURNS SETOF StationAndPoints
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT station_crs, station_name, ARRAY_AGG(station_point)
    FROM (
        SELECT
            TrainStationPoint.station_crs,
            station_name,
            (platform, latitude, longitude)::StationLatLon AS station_point
        FROM TrainStationPoint
        INNER JOIN TrainStation
        ON TrainStationPoint.station_crs = TrainStation.station_crs
    )
    GROUP BY (station_crs, station_name);
END;
$$;

CREATE OR REPLACE FUNCTION GetOperatorBrands(
    p_operator_code TEXT,
    p_run_date TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF TrainBrandOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        TrainBrand.train_brand_id,
        TrainBrand.brand_code,
        TrainBrand.brand_name,
        TrainBrand.bg_colour,
        TrainBrand.fg_colour
    FROM TrainBrand
    INNER JOIN TrainOperator
    ON TrainBrand.parent_operator = TrainOperator.train_operator_id
    WHERE p_operator_code = TrainOperator.operator_code
    AND operation_range @> p_run_date::date
    ORDER BY TrainBrand.brand_name;
END;
$$;

CREATE OR REPLACE FUNCTION GetStockCars(
    p_stock_class INT,
    p_stock_subclass INT,
    p_operator_code CHARACTER(2),
    p_brand_code CHARACTER(2),
    p_run_date TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF INT
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
        SELECT DISTINCT TrainStockFormation.cars
        FROM TrainStockFormation
        INNER JOIN (
            SELECT TrainStock.stock_class, TrainStockSubclass.stock_subclass
            FROM stock
            LEFT JOIN TrainStockSubclass
            ON TrainStock.stock_class = TrainStockSubclass.stock_class
        ) Stocks
        ON TrainStockFormation.stock_class = Stocks.stock_class
        AND (
            (Stocks.stock_subclass = TrainStockFormation.stock_subclass)
            OR (
                Stocks.stock_subclass IS NULL
                AND TrainStockFormation.stock_subclass IS NULL
            )
        )
        INNER JOIN TrainOperatorStock
        ON Stocks.stock_class = TrainOperatorStock.stock_class
        AND (
            (Stocks.stock_subclass = TrainOperatorStock.stock_subclass)
            OR (
                Stocks.stock_subclass IS NULL
                AND TrainOperatorStock.stock_subclass IS NULL
            )
        )
        INNER JOIN TrainOperator
        ON TrainOperatorStock.train_operator_id = TrainOperator.train_operator_id
        LEFT JOIN TrainBrand
        ON TrainOperatorStock.train_brand_id = TrainBrand.train_brand_id
        WHERE Stocks.stock_class = p_stock_class
        AND TrainOperator.operator_code = p_operator_code
        AND TrainOperator.operation_range @> p_run_date::DATE
        AND (p_brand_code IS NULL OR TrainBrand.brand_code = p_brand_code)
        AND (p_stock_subclass IS NULL OR Stocks.stock_subclass = p_stock_subclass)
        ORDER BY TrainStockFormation.cars ASC;
END;
$$;
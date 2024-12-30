CREATE OR REPLACE FUNCTION SelectCallAssocData()
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
        LEFT JOIN (SELECT * FROM SelectCallStockInfo()) StockDetails
        ON LegCall.dep_call_id = StockDetails.start_call
        LEFT JOIN (SELECT * FROM SelectCallAssocData()) CallAssocs
        ON ArrCall.call_id = CallAssocs.call_id
        ORDER BY COALESCE(ArrCall.plan_arr, ArrCall.act_arr, DepCall.plan_dep, DepCall.act_arr) ASC
    )
    SELECT LegCallData.leg_id, ARRAY_AGG(LegCallData.legcall_data) AS leg_calls
    FROM LegCallData
    GROUP BY LegCallData.leg_id;
END;
$$;

CREATE OR REPLACE FUNCTION SelectLegs(
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
    INNER JOIN (SELECT * FROM SelectLegCalls()) legcall_table
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
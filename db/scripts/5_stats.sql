CREATE OR REPLACE FUNCTION GetLegIdsInRange(
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE(leg_id INTEGER, start_time TIMESTAMP WITH TIME ZONE)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        Leg.leg_id,
        LegEnds.start_time
    FROM Leg
    INNER JOIN (
        SELECT
            LegCall.leg_id,
            MIN(
                COALESCE(Call.act_dep, Call.act_arr, Call.plan_dep, Call.plan_arr)
            ) AS start_time
        FROM LegCall
        INNER JOIN Call
        ON COALESCE(LegCall.dep_call_id, LegCall.arr_call_id) = Call.call_id
        GROUP BY LegCall.leg_id
    ) LegEnds
    ON Leg.leg_id = LegEnds.leg_id
    WHERE (p_start_date IS NULL OR LegEnds.start_time >= p_start_date)
    AND (p_end_date IS NULL OR LegEnds.start_time <= p_end_date)
    ORDER BY LegEnds.start_time;
END;
$$;

CREATE OR REPLACE FUNCTION GetStationCalls(
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    station_crs CHARACTER(3),
    calls BIGINT
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT StationCall.station_crs, StationCall.count FROM (
        SELECT Call.station_crs, COUNT(*) AS count
        FROM (SELECT * FROM GetLegIdsInRange(p_start_date, p_end_date)) LegId
        INNER JOIN LegCall
        ON LegId.leg_id = LegCall.leg_id
        INNER JOIN Call
        ON Call.call_id = COALESCE(LegCall.arr_call_id, LegCall.dep_call_id)
        GROUP BY Call.station_crs
    ) StationCall
    ORDER BY StationCall.count DESC;
END;
$$;

CREATE OR REPLACE FUNCTION GetStationStats (
    p_start_time TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_time TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE(
    station_crs CHARACTER(3),
    station_name TEXT,
    boards BIGINT,
    alights BIGINT,
    intermediates BIGINT
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        StationCount.station_crs,
        StationCount.station_name,
        StationCount.boards,
        StationCount.alights,
        StationCount.intermediates
    FROM (
        SELECT
            StationCount.station_crs,
            Station.station_name,
            StationCount.boards,
            StationCount.alights,
            (
                StationCount.calls -
                StationCount.boards -
                StationCount.alights
            ) AS intermediates
        FROM (
            WITH LegEndpoint AS (
                SELECT * FROM GetLegData(p_start_time, p_end_time)
            )
            SELECT
                LegCallCount.station_crs AS station_crs,
                COALESCE(StationBoardAlight.boards, 0) AS boards,
                COALESCE(StationBoardAlight.alights, 0) AS alights,
                COALESCE(LegCallCount.calls, 0) AS calls
            FROM (
                SELECT
                    COALESCE(
                        LegBoardCount.board_station_crs,
                        LegAlightCount.alight_station_crs
                    ) AS station_crs,
                    COALESCE(LegBoardCount.boards, 0) AS boards,
                    COALESCE(LegAlightCount.alights, 0) AS alights
                FROM (
                    SELECT LegEndpoint.board_station_crs, COUNT(*) AS boards
                    FROM LegEndpoint
                    GROUP BY LegEndpoint.board_station_crs
                ) LegBoardCount
                FULL OUTER JOIN (
                    SELECT LegEndpoint.alight_station_crs, COUNT(*) AS alights
                    FROM LegEndpoint
                    GROUP BY LegEndpoint.alight_station_crs
                ) LegAlightCount
                ON
                    LegBoardCount.board_station_crs =
                    LegAlightCount.alight_station_crs
            ) StationBoardAlight
            FULL OUTER JOIN (
                SELECT * FROM GetStationCalls(p_start_time, p_end_time)
            ) LegCallCount
            ON LegCallCount.station_crs = StationBoardAlight.station_crs
        ) StationCount
        INNER JOIN Station
        ON StationCount.station_crs = Station.station_crs
    ) StationCount
    ORDER BY
        (StationCount.boards + StationCount.alights) DESC,
        StationCount.boards DESC,
        StationCount.alights DESC,
        StationCount.intermediates DESC;
END;
$$;

CREATE OR REPLACE FUNCTION GetLegCallOverview (
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    leg_id INTEGER,
    board_call_id INTEGER,
    board_station_crs CHARACTER(3),
    alight_call_id INTEGER,
    alight_station_crs CHARACTER(3),
    intermediate_calls BIGINT
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        LegStopOverview.leg_id,
        LegStopOverview.board_call_id,
        LegStopOverview.board_station_crs,
        LegStopOverview.alight_call_id,
        LegStopOverview.alight_station_crs,
        LegStopOverview.intermediate_calls
    FROM (
        WITH LegStop AS (
            SELECT
                LegRange.leg_id,
                Call.call_id,
                Call.station_crs,
                COALESCE(plan_arr, plan_dep, act_arr, act_dep) AS stop_time
            FROM (SELECT * FROM GetLegIdsInRange(p_start_date, p_end_date)) LegRange
            INNER JOIN LegCall
            ON LegRange.leg_id = LegCall.leg_id
            INNER JOIN Call
            ON COALESCE(LegCall.arr_call_id, LegCall.dep_call_id) = Call.call_id
        )
        SELECT
            LegStopBoard.leg_id,
            LegStopBoardStation.call_id AS board_call_id,
            LegStopBoardStation.station_crs AS board_station_crs,
            LegStopAlightStation.call_id AS alight_call_id,
            LegStopAlightStation.station_crs AS alight_station_crs,
            LegStopIntermediate.intermediate_calls AS intermediate_calls
        FROM (
            SELECT LegStop.leg_id, MIN(stop_time) AS board_time
            FROM LegStop
            GROUP BY LegStop.leg_id
        ) LegStopBoard
        INNER JOIN (
            SELECT LegStop.leg_id, MAX(stop_time) AS alight_time
            FROM LegStop
            GROUP BY LegStop.leg_id
        ) LegStopAlight
        ON LegStopBoard.leg_id = LegStopAlight.leg_id
        INNER JOIN (
            SELECT LegStop.call_id, LegStop.stop_time, LegStop.station_crs
            FROM LegStop
        ) LegStopBoardStation
        ON LegStopBoardStation.stop_time = LegStopBoard.board_time
        INNER JOIN (
            SELECT LegStop.call_id, LegStop.stop_time, LegStop.station_crs
            FROM LegStop
        ) LegStopAlightStation
        ON LegStopAlightStation.stop_time = LegStopAlight.alight_time
        INNER JOIN (
            SELECT LegStop.leg_id, COUNT(*) - 2 AS intermediate_calls
            FROM LegStop
            GROUP BY LegStop.leg_id
        ) LegStopIntermediate
        ON LegStopIntermediate.leg_id = LegStopBoard.leg_id
    ) LegStopOverview;
END;
$$;

CREATE OR REPLACE FUNCTION GetLegStats (
    p_start_time TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_time TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    leg_id INTEGER,
    leg_start TIMESTAMP WITH TIME ZONE,
    board_crs CHARACTER(3),
    board_name TEXT,
    leg_end TIMESTAMP WITH TIME ZONE,
    alight_crs CHARACTER(3),
    alight_name TEXT,
    distance DECIMAL,
    duration INTERVAL,
    delay INTEGER,
    operator TEXT
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        LegStat.leg_id,
        LegStat.leg_start,
        LegStat.board_station_crs,
        LegStat.board_station_name,
        LegStat.leg_end,
        LegStat.alight_station_crs,
        LegStat.alight_station_name,
        LegStat.distance,
        LegStat.duration,
        LegStat.delay,
        LegStat.operator
    FROM (
        SELECT
            LegCallOverview.leg_id,
            COALESCE(
                BoardCall.act_dep,
                BoardCall.act_arr,
                BoardCall.plan_dep,
                BoardCall.plan_arr
            ) AS leg_start,
            LegCallOverview.board_station_crs,
            BoardStation.station_name AS board_station_name,
            COALESCE(
                AlightCall.act_dep,
                AlightCall.act_arr,
                AlightCall.plan_dep,
                AlightCall.plan_arr
            ) AS leg_end,
            LegCallOverview.alight_station_crs,
            AlightStation.station_name AS alight_station_name,
            COALESCE(
                AlightCall.mileage - BoardCall.mileage,
                Leg.distance
            ) AS distance,
            COALESCE(AlightCall.act_arr, AlightCall.plan_arr)
            -
            COALESCE(BoardCall.act_dep, BoardCall.plan_dep) AS duration,
            (EXTRACT(
                EPOCH FROM (
                    COALESCE(AlightCall.act_arr, AlightCall.act_dep)
                    -
                    COALESCE(AlightCall.plan_arr, AlightCall.plan_dep)
                )
            ) / 60)::INTEGER AS delay,
            COALESCE(Brand.brand_name, Operator.operator_name) AS operator
        FROM (
            SELECT * FROM GetLegCallOverview(p_start_time, p_end_time)
        ) LegCallOverview
        INNER JOIN Station BoardStation
        ON LegCallOverview.board_station_crs = BoardStation.station_crs
        INNER JOIN Station AlightStation
        ON LegCallOverview.alight_station_crs = AlightStation.station_crs
        INNER JOIN Call BoardCall
        ON LegCallOverview.board_call_id = BoardCall.call_id
        INNER JOIN Call AlightCall
        ON LegCallOverview.alight_call_id = AlightCall.call_id
        INNER JOIN Leg
        ON LegCallOverview.leg_id = Leg.leg_id
        INNER JOIN Service
        ON BoardCall.service_id = Service.service_id
        AND BoardCall.run_date = Service.run_date
        INNER JOIN Operator
        ON Service.operator_id = Operator.operator_id
        LEFT JOIN Brand
        ON Service.brand_id = Brand.brand_id
    ) LegStat
    ORDER BY LegStat.leg_start;
END;
$$;

CREATE OR REPLACE FUNCTION GetStockUsed(
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    leg_id INTEGER,
    stock_class INTEGER,
    stock_subclass INTEGER,
    stock_number INTEGER
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        Leg.leg_id,
        StockReport.stock_class,
        StockReport.stock_subclass,
        StockReport.stock_number
    FROM Leg
    INNER JOIN LegCall
    ON Leg.leg_id = LegCall.leg_id
    INNER JOIN Call
    ON LegCall.arr_call_id = Call.call_id
    OR LegCall.dep_call_id = Call.call_id
    INNER JOIN StockSegment
    ON Call.call_id = StockSegment.start_call
    INNER JOIN StockSegmentReport
    ON StockSegment.stock_segment_id = StockSegmentReport.stock_segment_id
    INNER JOIN StockReport
    ON StockSegmentReport.stock_report_id = StockReport.stock_report_id
    INNER JOIN GetLegIdsInRange(p_start_date, p_end_date) LegId
    ON Leg.leg_id = LegId.leg_id;
END;
$$;

CREATE OR REPLACE FUNCTION GetClassStats(
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    stock_class INTEGER,
    count BIGINT
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT LegClass.stock_class, COUNT(*)
    FROM (
        SELECT DISTINCT LegStock.leg_id, LegStock.stock_class
        FROM GetStockUsed(p_start_date, p_end_date) LegStock
    ) LegClass
    GROUP BY LegClass.stock_class
    ORDER BY count DESC;
END;
$$;

CREATE OR REPLACE FUNCTION GetUnitStats(
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    stock_number INTEGER,
    count BIGINT
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT LegStock.stock_number, COUNT(*)
    FROM GetStockUsed(p_start_date, p_end_date) LegStock
    WHERE LegStock.stock_number IS NOT NULL
    GROUP BY LegStock.stock_number
    ORDER BY count DESC;
END;
$$;

CREATE OR REPLACE FUNCTION GetOperatorStats (
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    operator TEXT,
    count BIGINT,
    distance DECIMAL,
    duration INTERVAL,
    delay BIGINT
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        LegStat.operator,
        COUNT(*) AS count,
        SUM(LegStat.distance) AS distance,
        SUM(LegStat.duration) AS duration,
        SUM(LegStat.delay) AS delay
    FROM (SELECT * FROM GetLegStats(p_start_date, p_end_date)) LegStat
    GROUP BY LegStat.operator
    ORDER BY count DESC;
END;
$$;


CREATE OR REPLACE FUNCTION GetLegDelayRanking (
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    run_date TIMESTAMP WITH TIME ZONE,
    board_name TEXT,
    alight_name TEXT,
    delay INTEGER
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT LegStat.run_date, LegStat.board_name, LegStat.alight_name, LegStat.delay
    FROM (SELECT * FROM GetLegStats(p_start_date, p_end_date)) LegStat
    WHERE LegStat.delay IS NOT NULL
    ORDER BY LegStat.delay DESC;
END;
$$;

CREATE OR REPLACE FUNCTION GetLegDistanceRanking (
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    run_date TIMESTAMP WITH TIME ZONE,
    board_name TEXT,
    alight_name TEXT,
    distance DECIMAL
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT LegStat.run_date, LegStat.board_name, LegStat.alight_name, LegStat.distance
    FROM (SELECT * FROM GetLegStats(p_start_date, p_end_date)) LegStat
    WHERE LegStat.distance IS NOT NULL
    ORDER BY LegStat.distance DESC;
END;
$$;

CREATE OR REPLACE FUNCTION GetLegDurationRanking (
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    run_date TIMESTAMP WITH TIME ZONE,
    board_name TEXT,
    alight_name TEXT,
    duration INTERVAL
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT LegStat.run_date, LegStat.board_name, LegStat.alight_name, LegStat.duration
    FROM (SELECT * FROM GetLegStats(p_start_date, p_end_date)) LegStat
    WHERE LegStat.duration IS NOT NULL
    ORDER BY LegStat.duration DESC;
END;
$$;
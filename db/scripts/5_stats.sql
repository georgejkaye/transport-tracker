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
        LegStart.start_time
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
    ) LegStart
    ON Leg.leg_id = LegStart.leg_id
    WHERE (p_start_date IS NULL OR LegStart.start_time >= p_start_date)
    AND (p_end_date IS NULL OR LegStart.start_time <= p_end_date)
    ORDER BY LegStart.start_time;
END;
$$;

CREATE OR REPLACE FUNCTION GetLegCalls(
    p_start_date TIMESTAMP WITH TIME ZONE,
    p_end_date TIMESTAMP WITH TIME ZONE
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

CREATE OR REPLACE FUNCTION GetLegOverview(
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    leg_id INTEGER,
    service_id TEXT,
    leg_start TIMESTAMP WITH TIME ZONE,
    board_call_id INTEGER,
    board_station_crs CHARACTER(3),
    alight_call_id INTEGER,
    alight_station_crs CHARACTER(3),
    intermediate_calls BIGINT,
    operator TEXT
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        LegStopOverview.leg_id,
        Service.service_id,
        LegStart.leg_start,
        LegStopOverview.board_call_id,
        LegStopOverview.board_station_crs,
        LegStopOverview.alight_call_id,
        LegStopOverview.alight_station_crs,
        LegStopOverview.intermediate_calls,
        COALESCE(Brand.brand_name, Operator.operator_name) AS operator
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
    ) LegStopOverview
    INNER JOIN (
        SELECT Leg.leg_id, MIN(
            COALESCE(
                Call.act_dep,
                Call.act_arr,
                Call.plan_dep,
                Call.plan_arr
            )
        ) AS leg_start
        FROM Leg
        INNER JOIN LegCall
        ON Leg.leg_id = LegCall.leg_id
        INNER JOIN Call
        ON LegCall.arr_call_id = Call.call_id
        OR LegCall.dep_call_id = Call.call_id
        GROUP BY Leg.leg_id
    ) LegStart
    ON LegStopOverview.leg_id = LegStart.leg_id
    INNER JOIN Call
    ON LegStopOverview.board_call_id = Call.call_id
    INNER JOIN Service
    ON Call.service_id = Service.service_id
    AND Call.run_date = Service.run_date
    INNER JOIN Operator
    ON Service.operator_id = Operator.operator_id
    LEFT JOIN Brand
    ON Service.brand_id = Brand.brand_id
    ORDER BY LegStart.leg_start;
END;
$$;

CREATE OR REPLACE FUNCTION GetStationCounts(
    p_start_time TIMESTAMP WITH TIME ZONE,
    p_end_time TIMESTAMP WITH TIME ZONE
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
            (StationCount.calls - StationCount.boards - StationCount.alights) AS intermediates
        FROM (
            WITH LegEndpoint AS (SELECT * FROM GetLegOverview(p_start_time, p_end_time))
            SELECT
                LegCallCount.station_crs AS station_crs,
                COALESCE(StationBoardAlight.boards, 0) AS boards,
                COALESCE(StationBoardAlight.alights, 0) AS alights,
                COALESCE(LegCallCount.calls, 0) AS calls
            FROM (
                SELECT
                    COALESCE(LegBoardCount.board_station_crs, LegAlightCount.alight_station_crs) AS station_crs,
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
                ON LegBoardCount.board_station_crs = LegAlightCount.alight_station_crs
            ) StationBoardAlight
            FULL OUTER JOIN (SELECT * FROM GetLegCalls(p_start_time, p_end_time)) LegCallCount
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


CREATE OR REPLACE FUNCTION GetStationVisits(
    p_start_time TIMESTAMP WITH TIME ZONE,
    p_end_time TIMESTAMP WITH TIME ZONE
)
RETURNS TABLE(
    station_crs CHARACTER(3),
    station_name TEXT,
    visits BIGINT
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        StationCount.station_crs,
        StationCount.station_name,
        (StationCount.boards + StationCount.alights) AS visits
    FROM (
        SELECT * FROM GetStationCounts(p_start_time, p_end_time)
    ) StationCount;
END;
$$;

CREATE OR REPLACE FUNCTION GetLegStats (
    p_start_time TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_time TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    leg_id INTEGER,
    run_date TIMESTAMP WITH TIME ZONE,
    board_crs CHARACTER(3),
    board_name TEXT,
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
        LegOverview.leg_id,
        LegOverview.leg_start,
        LegOverview.board_station_crs,
        BoardStation.station_name,
        LegOverview.alight_station_crs,
        AlightStation.station_name,
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
        LegOverview.operator
    FROM (SELECT * FROM GetLegOverview(p_start_time, p_end_time)) LegOverview
    INNER JOIN Station BoardStation
    ON LegOverview.board_station_crs = BoardStation.station_crs
    INNER JOIN Station AlightStation
    ON LegOverview.alight_station_crs = AlightStation.station_crs
    INNER JOIN Call BoardCall
    ON LegOverview.board_call_id = BoardCall.call_id
    INNER JOIN Call AlightCall
    ON LegOverview.alight_call_id = AlightCall.call_id
    INNER JOIN Leg
    ON LegOverview.leg_id = Leg.leg_id
    ORDER BY LegOverview.leg_start;
END;
$$;
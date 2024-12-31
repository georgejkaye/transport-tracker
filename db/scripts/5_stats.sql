CREATE OR REPLACE FUNCTION GetLegStartTime(
    p_leg_id INTEGER
)
RETURNS TIMESTAMP WITH TIME ZONE
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN (
        SELECT MIN(
            COALESCE(
                Call.act_dep,
                Call.act_arr,
                Call.plan_dep,
                Call.plan_arr
            )
        )
        FROM Leg
        INNER JOIN LegCall
        ON Leg.leg_id = LegCall.leg_id
        INNER JOIN Call
        ON LegCall.arr_call_id = Call.call_id
        OR LegCall.dep_call_id = Call.call_id
        WHERE Leg.leg_id = p_leg_id
    );
END;
$$;

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
    SELECT LegStart.leg_id, LegStart.start_time FROM (
        SELECT Leg.leg_id, GetLegStartTime(Leg.leg_id) AS start_time FROM Leg
    ) LegStart
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

CREATE OR REPLACE FUNCTION GetLegCallStats(
    p_start_date TIMESTAMP WITH TIME ZONE,
    p_end_date TIMESTAMP WITH TIME ZONE
)
RETURNS TABLE (
    leg_id INTEGER,
    board_station_crs CHARACTER(3),
    alight_station_crs CHARACTER(3),
    intermediate_calls BIGINT
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH LegRange AS (SELECT * FROM GetLegIdsInRange(p_start_date, p_end_date)),
    LegStop AS (
        SELECT
            LegRange.leg_id,
            Call.station_crs,
            COALESCE(plan_arr, plan_dep, act_arr, act_dep) AS stop_time
        FROM LegRange
        INNER JOIN LegCall
        ON LegRange.leg_id = LegCall.leg_id
        INNER JOIN Call
        ON COALESCE(LegCall.arr_call_id, LegCall.dep_call_id) = Call.call_id
    )
    SELECT
        LegStopBoard.leg_id,
        LegStopBoardStation.station_crs AS board_station_crs,
        LegStopAlightStation.station_crs AS alight_station_crs,
        LegStopIntermediate.intermediate_calls AS call_station_count
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
        SELECT LegStop.stop_time, LegStop.station_crs
        FROM LegStop
    ) LegStopBoardStation
    ON LegStopBoardStation.stop_time = LegStopBoard.board_time
    INNER JOIN (
        SELECT LegStop.stop_time, LegStop.station_crs
        FROM LegStop
    ) LegStopAlightStation
    ON LegStopAlightStation.stop_time = LegStopAlight.alight_time
    INNER JOIN (
        SELECT LegStop.leg_id, COUNT(*) - 2 AS intermediate_calls
        FROM LegStop
        GROUP BY LegStop.leg_id
    ) LegStopIntermediate
    ON LegStopIntermediate.leg_id = LegStopBoard.leg_id;
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
            WITH LegEndpoint AS (SELECT * FROM GetLegCallStats(p_start_time, p_end_time))
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
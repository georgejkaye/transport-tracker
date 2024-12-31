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
    WHERE LegStart.start_time >= p_start_date
    AND LegStart.start_time <= p_end_date
    ORDER BY LegStart.start_time;
END;
$$;

CREATE OR REPLACE FUNCTION GetLegBoards()
RETURNS TABLE (leg_id INTEGER, station_crs CHARACTER(3))
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT Leg.leg_id, Call.call_id, COALESCE(plan_arr, plan_dep, act_arr, act_dep) AS stop_time
    FROM Leg
    INNER JOIN LegCall
    ON Leg.leg_id = LegCall.leg_id
    INNER JOIN Call
    ON COALESCE(LegCall.arr_call_id, LegCall.dep_call_id) = Call.call_id


CREATE OR REPLACE FUNCTION GetMostVisitedStations(
    leg_ids TABLE (leg_id INTEGER)
    start_date TIMESTAMP WITH TIME ZONE NULL,
    end_date TIMESTAMP WITH TIME ZONE NULL
)
RETURNS TABLE(
    station_crs CHARACTER(3),
    station_name TEXT,
    total_visits INTEGER
)
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
END;
$$;
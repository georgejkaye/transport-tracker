CREATE OR REPLACE FUNCTION select_bus_leg_user_details (
    p_user_id INTEGER_NOTNULL
)
RETURNS SETOF bus_leg_user_details
LANGUAGE sql
AS
$$
SELECT
    bus_leg_user_details_view.leg_id,
    bus_leg_user_details_view.leg_service,
    bus_leg_user_details_view.leg_vehicle,
    bus_leg_user_details_view.leg_calls,
    bus_leg_user_details_view.leg_duration
FROM bus_leg_user_details_view
WHERE bus_leg_user_details_view.user_id = p_user_id
$$;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details_by_user_id_and_datetime (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP_NOTNULL,
    p_search_end TIMESTAMP_NOTNULL
)
RETURNS SETOF bus_leg_user_details
LANGUAGE sql
AS
$$
SELECT
    bus_leg_user_details_view.leg_id,
    bus_leg_user_details_view.leg_service,
    bus_leg_user_details_view.leg_vehicle,
    bus_leg_user_details_view.leg_calls,
    bus_leg_user_details_view.leg_duration
FROM bus_leg_user_details_view
WHERE bus_leg_user_details_view.user_id = p_user_id
AND COALESCE(
    (bus_leg_user_details_view.leg_calls)[1].plan_dep,
    (bus_leg_user_details_view.leg_calls)[1].act_dep,
    (bus_leg_user_details_view.leg_calls)[1].plan_arr,
    (bus_leg_user_details_view.leg_calls)[1].act_arr) >= p_search_start
AND COALESCE(
    (bus_leg_user_details_view.leg_calls)[1].plan_dep,
    (bus_leg_user_details_view.leg_calls)[1].act_dep,
    (bus_leg_user_details_view.leg_calls)[1].plan_arr,
    (bus_leg_user_details_view.leg_calls)[1].act_arr) < p_search_end;
$$;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details_by_user_id_and_start_datetime (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP_NOTNULL
)
RETURNS SETOF bus_leg_user_details
LANGUAGE sql
AS
$$
SELECT
    bus_leg_user_details_view.leg_id,
    bus_leg_user_details_view.leg_service,
    bus_leg_user_details_view.leg_vehicle,
    bus_leg_user_details_view.leg_calls,
    bus_leg_user_details_view.leg_duration
FROM bus_leg_user_details_view
WHERE bus_leg_user_details_view.user_id = p_user_id
AND COALESCE(
    (bus_leg_user_details_view.leg_calls)[1].plan_dep,
    (bus_leg_user_details_view.leg_calls)[1].act_dep,
    (bus_leg_user_details_view.leg_calls)[1].plan_arr,
    (bus_leg_user_details_view.leg_calls)[1].act_arr) >= p_search_start;
$$;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details_by_user_id_and_end_datetime (
    p_user_id INTEGER_NOTNULL,
    p_search_end TIMESTAMP_NOTNULL
)
RETURNS SETOF bus_leg_user_details
LANGUAGE sql
AS
$$
SELECT
    bus_leg_user_details_view.leg_id,
    bus_leg_user_details_view.leg_service,
    bus_leg_user_details_view.leg_vehicle,
    bus_leg_user_details_view.leg_calls,
    bus_leg_user_details_view.leg_duration
FROM bus_leg_user_details_view
WHERE bus_leg_user_details_view.user_id = p_user_id
AND COALESCE(
    (bus_leg_user_details_view.leg_calls)[1].plan_dep,
    (bus_leg_user_details_view.leg_calls)[1].act_dep,
    (bus_leg_user_details_view.leg_calls)[1].plan_arr,
    (bus_leg_user_details_view.leg_calls)[1].act_arr) <= p_search_end;
$$;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details_by_user_id_and_leg_id (
    p_user_id INTEGER_NOTNULL,
    p_leg_id INTEGER_NOTNULL
)
RETURNS SETOF bus_leg_user_details
LANGUAGE sql
AS
$$
SELECT
    bus_leg_user_details_view.leg_id,
    bus_leg_user_details_view.leg_service,
    bus_leg_user_details_view.leg_vehicle,
    bus_leg_user_details_view.leg_calls,
    bus_leg_user_details_view.leg_duration
FROM bus_leg_user_details_view
WHERE bus_leg_user_details_view.user_id = p_user_id
AND bus_leg_user_details_view.leg_id = p_leg_id
$$;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details_by_user_id_and_leg_ids (
    p_user_id INTEGER_NOTNULL,
    p_leg_ids INTEGER_NOTNULL[]
)
RETURNS SETOF bus_leg_user_details
LANGUAGE sql
AS
$$
SELECT
    bus_leg_user_details_view.leg_id,
    bus_leg_user_details_view.leg_service,
    bus_leg_user_details_view.leg_vehicle,
    bus_leg_user_details_view.leg_calls,
    bus_leg_user_details_view.leg_duration
FROM bus_leg_user_details_view
WHERE bus_leg_user_details_view.user_id = p_user_id
AND bus_leg_user_details_view.leg_id = ANY(P_leg_ids);
$$;
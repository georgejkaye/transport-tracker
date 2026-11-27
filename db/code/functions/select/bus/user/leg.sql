CREATE OR REPLACE FUNCTION select_bus_leg_user_details (
    p_user_id INTEGER_NOTNULL
)
RETURNS SETOF bus_leg_summary
LANGUAGE sql
AS
$$
SELECT
    transport_user_bus_leg_summary_view.bus_leg_id,
    transport_user_bus_leg_summary_view.operator,
    transport_user_bus_leg_summary_view.services,
    transport_user_bus_leg_summary_view.vehicle,
    transport_user_bus_leg_summary_view.board_stop,
    transport_user_bus_leg_summary_view.alight_stop,
    transport_user_bus_leg_summary_view.duration
FROM transport_user_bus_leg_summary_view
WHERE transport_user_bus_leg_summary_view.user_id = p_user_id
$$;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details_by_user_id_and_datetime (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP_NOTNULL,
    p_search_end TIMESTAMP_NOTNULL
)
RETURNS SETOF bus_leg_summary
LANGUAGE sql
AS
$$
SELECT
    transport_user_bus_leg_summary_view.bus_leg_id,
    transport_user_bus_leg_summary_view.operator,
    transport_user_bus_leg_summary_view.services,
    transport_user_bus_leg_summary_view.vehicle,
    transport_user_bus_leg_summary_view.board_stop,
    transport_user_bus_leg_summary_view.alight_stop,
    transport_user_bus_leg_summary_view.duration
FROM transport_user_bus_leg_summary_view
WHERE transport_user_bus_leg_summary_view.user_id = p_user_id
AND COALESCE(
    (transport_user_bus_leg_summary_view.board_stop).plan_dep,
    (transport_user_bus_leg_summary_view.board_stop).act_dep
) >= p_search_start
AND COALESCE(
    (transport_user_bus_leg_summary_view.alight_stop).plan_arr,
    (transport_user_bus_leg_summary_view.alight_stop).act_arr
) < p_search_end;
$$;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details_by_user_id_and_start_datetime (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP_NOTNULL
)
RETURNS SETOF bus_leg_summary
LANGUAGE sql
AS
$$
SELECT
    transport_user_bus_leg_summary_view.bus_leg_id,
    transport_user_bus_leg_summary_view.operator,
    transport_user_bus_leg_summary_view.services,
    transport_user_bus_leg_summary_view.vehicle,
    transport_user_bus_leg_summary_view.board_stop,
    transport_user_bus_leg_summary_view.alight_stop,
    transport_user_bus_leg_summary_view.duration
FROM transport_user_bus_leg_summary_view
WHERE transport_user_bus_leg_summary_view.user_id = p_user_id
AND COALESCE(
    (transport_user_bus_leg_summary_view.board_stop).plan_dep,
    (transport_user_bus_leg_summary_view.board_stop).act_dep
) >= p_search_start;
$$;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details_by_user_id_and_end_datetime (
    p_user_id INTEGER_NOTNULL,
    p_search_end TIMESTAMP_NOTNULL
)
RETURNS SETOF bus_leg_summary
LANGUAGE sql
AS
$$
SELECT
    transport_user_bus_leg_summary_view.bus_leg_id,
    transport_user_bus_leg_summary_view.operator,
    transport_user_bus_leg_summary_view.services,
    transport_user_bus_leg_summary_view.vehicle,
    transport_user_bus_leg_summary_view.board_stop,
    transport_user_bus_leg_summary_view.alight_stop,
    transport_user_bus_leg_summary_view.duration
FROM transport_user_bus_leg_summary_view
WHERE transport_user_bus_leg_summary_view.user_id = p_user_id
AND COALESCE(
    (transport_user_bus_leg_summary_view.alight_stop).plan_arr,
    (transport_user_bus_leg_summary_view.alight_stop).act_arr
) < p_search_end;
$$;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details_by_user_id_and_leg_id (
    p_user_id INTEGER_NOTNULL,
    p_leg_id INTEGER_NOTNULL
)
RETURNS SETOF bus_leg_details
LANGUAGE sql
AS
$$
SELECT
    transport_user_bus_leg_details_view.leg_id,
    transport_user_bus_leg_details_view.operator,
    transport_user_bus_leg_details_view.journeys,
    transport_user_bus_leg_details_view.vehicle,
    transport_user_bus_leg_details_view.calls,
    transport_user_bus_leg_details_view.duration
FROM transport_user_bus_leg_details_view
WHERE transport_user_bus_leg_details_view.user_id = p_user_id
AND transport_user_bus_leg_details_view.leg_id = p_leg_id
$$;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details_by_user_id_and_leg_ids (
    p_user_id INTEGER_NOTNULL,
    p_leg_ids INTEGER_NOTNULL[]
)
RETURNS SETOF bus_leg_details
LANGUAGE sql
AS
$$
SELECT
    transport_user_bus_leg_details_view.leg_id,
    transport_user_bus_leg_details_view.operator,
    transport_user_bus_leg_details_view.journeys,
    transport_user_bus_leg_details_view.vehicle,
    transport_user_bus_leg_details_view.calls,
    transport_user_bus_leg_details_view.duration
FROM transport_user_bus_leg_details_view
WHERE transport_user_bus_leg_details_view.user_id = p_user_id
AND transport_user_bus_leg_details_view.leg_id = ANY(p_leg_ids);
$$;
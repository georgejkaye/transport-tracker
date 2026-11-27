CREATE OR REPLACE FUNCTION select_transport_user_bus_stop_details_by_user_id_and_stop_id (
    p_user_id INTEGER_NOTNULL,
    p_stop_id INTEGER_NOTNULL
)
RETURNS SETOF transport_user_bus_stop_details
LANGUAGE sql
AS
$$
SELECT
    bus_stop.bus_stop_id,
    bus_stop.atco_code,
    bus_stop.naptan_code,
    bus_stop.stop_name,
    bus_stop.landmark_name,
    bus_stop.street_name,
    bus_stop.indicator,
    bus_stop.bearing,
    bus_stop.locality_name,
    bus_stop.town_name,
    bus_stop.latitude,
    bus_stop.longitude,
    COALESCE(
        stop_leg_details.stop_user_legs,
        ARRAY[]::transport_user_bus_stop_leg_summary[]
    )
FROM bus_stop
LEFT JOIN LATERAL (
    SELECT ARRAY_AGG((
        stop_leg.bus_leg_id,
        stop_leg.operator,
        stop_leg.services,
        (
            board_call.bus_call_id,
            (
                board_stop.bus_stop_id,
                board_stop.atco_code,
                board_stop.stop_name,
                board_stop.locality_name,
                board_stop.street_name,
                board_stop.indicator
            )::bus_call_stop_details,
            board_call.plan_arr,
            board_call.act_arr,
            board_call.plan_dep,
            board_call.act_dep
        )::bus_call_details,
        (
            alight_call.bus_call_id,
            (
                alight_stop.bus_stop_id,
                alight_stop.atco_code,
                alight_stop.stop_name,
                alight_stop.locality_name,
                alight_stop.street_name,
                alight_stop.indicator
            )::bus_call_stop_details,
            alight_call.plan_arr,
            alight_call.act_arr,
            alight_call.plan_dep,
            alight_call.act_dep
        )::bus_call_details,
        (
            stop_leg.bus_call_id,
            (
                stop_leg.bus_stop_id,
                stop_leg.atco_code,
                stop_leg.stop_name,
                stop_leg.locality_name,
                stop_leg.street_name,
                stop_leg.indicator
            )::bus_call_stop_details,
            stop_leg.plan_arr,
            stop_leg.act_arr,
            stop_leg.plan_dep,
            stop_leg.act_dep
        )::bus_call_details,
        stop_leg.stops_before,
        stop_leg.stops_after
    )::transport_user_bus_stop_leg_summary ORDER BY stop_leg.effective_time)
    AS stop_user_legs
    FROM transport_user_bus_stop_leg_view stop_leg
    INNER JOIN bus_leg_journey
    ON bus_leg_journey.bus_leg_id = stop_leg.bus_leg_id
    AND bus_leg_journey.bus_journey_id = stop_leg.bus_journey_id
    INNER JOIN bus_call board_call
    ON board_call.bus_call_id = bus_leg_journey.start_call_id
    INNER JOIN bus_stop board_stop
    ON board_stop.bus_stop_id = board_call.bus_stop_id
    INNER JOIN bus_call alight_call
    ON alight_call.bus_call_id = bus_leg_journey.end_call_id
    INNER JOIN bus_stop alight_stop
    ON alight_stop.bus_stop_id = alight_call.bus_stop_id
    WHERE stop_leg.bus_stop_id = bus_stop.bus_stop_id
    AND stop_leg.user_id = p_user_id
) stop_leg_details ON TRUE
WHERE bus_stop.bus_stop_id = p_stop_id;
$$;

CREATE OR REPLACE FUNCTION select_transport_user_bus_stop_details_by_user_id_and_atco (
    p_user_id INTEGER_NOTNULL,
    p_atco TEXT_NOTNULL
)
RETURNS SETOF transport_user_bus_stop_details
LANGUAGE sql
AS
$$
SELECT
    bus_stop.bus_stop_id,
    bus_stop.atco_code,
    bus_stop.naptan_code,
    bus_stop.stop_name,
    bus_stop.landmark_name,
    bus_stop.street_name,
    bus_stop.indicator,
    bus_stop.bearing,
    bus_stop.locality_name,
    bus_stop.town_name,
    bus_stop.latitude,
    bus_stop.longitude,
    COALESCE(
        stop_leg_details.stop_user_legs,
        ARRAY[]::transport_user_bus_stop_leg_summary[]
    )
FROM bus_stop
LEFT JOIN LATERAL (
    SELECT ARRAY_AGG((
        stop_leg.bus_leg_id,
        stop_leg.operator,
        stop_leg.services,
        (
            board_call.bus_call_id,
            (
                board_stop.bus_stop_id,
                board_stop.atco_code,
                board_stop.stop_name,
                board_stop.locality_name,
                board_stop.street_name,
                board_stop.indicator
            )::bus_call_stop_details,
            board_call.plan_arr,
            board_call.act_arr,
            board_call.plan_dep,
            board_call.act_dep
        )::bus_call_details,
        (
            alight_call.bus_call_id,
            (
                alight_stop.bus_stop_id,
                alight_stop.atco_code,
                alight_stop.stop_name,
                alight_stop.locality_name,
                alight_stop.street_name,
                alight_stop.indicator
            )::bus_call_stop_details,
            alight_call.plan_arr,
            alight_call.act_arr,
            alight_call.plan_dep,
            alight_call.act_dep
        )::bus_call_details,
        (
            stop_leg.bus_call_id,
            (
                stop_leg.bus_stop_id,
                stop_leg.atco_code,
                stop_leg.stop_name,
                stop_leg.locality_name,
                stop_leg.street_name,
                stop_leg.indicator
            )::bus_call_stop_details,
            stop_leg.plan_arr,
            stop_leg.act_arr,
            stop_leg.plan_dep,
            stop_leg.act_dep
        )::bus_call_details,
        stop_leg.stops_before,
        stop_leg.stops_after
    )::transport_user_bus_stop_leg_summary ORDER BY stop_leg.effective_time)
    AS stop_user_legs
    FROM transport_user_bus_stop_leg_view stop_leg
    INNER JOIN bus_leg_journey
    ON bus_leg_journey.bus_leg_id = stop_leg.bus_leg_id
    AND bus_leg_journey.bus_journey_id = stop_leg.bus_journey_id
    INNER JOIN bus_call board_call
    ON board_call.bus_call_id = bus_leg_journey.start_call_id
    INNER JOIN bus_stop board_stop
    ON board_stop.bus_stop_id = board_call.bus_stop_id
    INNER JOIN bus_call alight_call
    ON alight_call.bus_call_id = bus_leg_journey.end_call_id
    INNER JOIN bus_stop alight_stop
    ON alight_stop.bus_stop_id = alight_call.bus_stop_id
    WHERE stop_leg.bus_stop_id = bus_stop.bus_stop_id
    AND stop_leg.user_id = p_user_id
) stop_leg_details ON TRUE
WHERE bus_stop.atco_code = p_atco;
$$;

CREATE OR REPLACE FUNCTION select_transport_user_bus_stop_details_by_user_id (
    p_user_id INTEGER_NOTNULL
)
RETURNS SETOF transport_user_bus_stop_summary
LANGUAGE sql
AS
$$
SELECT
    bus_stop.bus_stop_id,
    bus_stop.atco_code,
    bus_stop.naptan_code,
    bus_stop.stop_name,
    bus_stop.landmark_name,
    bus_stop.street_name,
    bus_stop.indicator,
    bus_stop.bearing,
    bus_stop.locality_name,
    bus_stop.town_name,
    bus_stop.latitude,
    bus_stop.longitude,
    stop_counts.boards,
    stop_counts.alights,
    stop_counts.total
        - stop_counts.boards
        - stop_counts.alights AS calls
FROM bus_stop
INNER JOIN (
    SELECT
        stop_leg.bus_stop_id,
        COUNT(*) AS total,
        COUNT(
            CASE
            WHEN stop_leg.bus_call_id = bus_leg_journey.start_call_id
            THEN 1
            END
        ) AS boards,
        COUNT(
            CASE
            WHEN stop_leg.bus_call_id = bus_leg_journey.end_call_id
            THEN 1
            END
        ) AS alights
    FROM transport_user_bus_stop_leg_view stop_leg
    INNER JOIN bus_leg_journey
    ON bus_leg_journey.bus_leg_id = stop_leg.bus_leg_id
    AND bus_leg_journey.bus_journey_id = stop_leg.bus_journey_id
    WHERE stop_leg.user_id = p_user_id
    GROUP BY stop_leg.bus_stop_id
) stop_counts
ON bus_stop.bus_stop_id = stop_counts.bus_stop_id
ORDER BY
    bus_stop.stop_name,
    bus_stop.locality_name,
    bus_stop.indicator;
$$;
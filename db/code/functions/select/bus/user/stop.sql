CREATE OR REPLACE FUNCTION select_bus_stop_user_details_by_user_id_and_stop_id (
    p_user_id INTEGER_NOTNULL,
    p_stop_id INTEGER_NOTNULL
)
RETURNS SETOF bus_stop_user_details
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
        ARRAY[]::bus_stop_leg_details[]
    )
FROM bus_stop
LEFT JOIN LATERAL (
    SELECT ARRAY_AGG((
        bus_leg_id,
        (
            bus_service_id,
            service_line,
            (
                bus_operator_id,
                operator_name,
                national_operator_code
            )::bus_operator_details,
            description_outbound,
            description_inbound
        )::bus_leg_service_details,
        (
            board_call_id,
            (
                board_stop_id,
                board_atco_code,
                board_stop_name,
                board_locality_name,
                board_street_name,
                board_indicator
            )::bus_call_stop_details,
            board_plan_arr,
            board_act_arr,
            board_plan_dep,
            board_act_dep
        )::bus_call_details,
        (
            alight_call_id,
            (
                alight_stop_id,
                alight_atco_code,
                alight_stop_name,
                alight_locality_name,
                alight_street_name,
                alight_indicator
            )::bus_call_stop_details,
            alight_plan_arr,
            alight_act_arr,
            alight_plan_dep,
            alight_act_dep
        )::bus_call_details,
        (
            bus_call_id,
            (
                bus_stop_id,
                atco_code,
                stop_name,
                locality_name,
                street_name,
                indicator
            )::bus_call_stop_details,
            plan_arr,
            act_arr,
            plan_dep,
            act_dep
        )::bus_call_details,
        stops_before,
        stops_after
    )::bus_stop_leg_details ORDER BY effective_time)
    AS stop_user_legs
    FROM transport_user_bus_stop_view
    WHERE bus_stop_id = bus_stop.bus_stop_id
    AND user_id = p_user_id
) stop_leg_details ON TRUE
WHERE bus_stop.bus_stop_id = p_stop_id;
$$;

CREATE OR REPLACE FUNCTION select_bus_stop_user_details_by_user_id_and_atco (
    p_user_id INTEGER_NOTNULL,
    p_atco TEXT_NOTNULL
)
RETURNS SETOF bus_stop_user_details
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
        ARRAY[]::bus_stop_leg_details[]
    )
FROM bus_stop
LEFT JOIN LATERAL (
    SELECT ARRAY_AGG((
        bus_leg_id,
        (
            bus_service_id,
            service_line,
            (
                bus_operator_id,
                operator_name,
                national_operator_code
            )::bus_operator_details,
            description_outbound,
            description_inbound
        )::bus_leg_service_details,
        (
            board_call_id,
            (
                board_stop_id,
                board_atco_code,
                board_stop_name,
                board_locality_name,
                board_street_name,
                board_indicator
            )::bus_call_stop_details,
            board_plan_arr,
            board_act_arr,
            board_plan_dep,
            board_act_dep
        )::bus_call_details,
        (
            alight_call_id,
            (
                alight_stop_id,
                alight_atco_code,
                alight_stop_name,
                alight_locality_name,
                alight_street_name,
                alight_indicator
            )::bus_call_stop_details,
            alight_plan_arr,
            alight_act_arr,
            alight_plan_dep,
            alight_act_dep
        )::bus_call_details,
        (
            bus_call_id,
            (
                bus_stop_id,
                atco_code,
                stop_name,
                locality_name,
                street_name,
                indicator
            )::bus_call_stop_details,
            plan_arr,
            act_arr,
            plan_dep,
            act_dep
        )::bus_call_details,
        stops_before,
        stops_after
    )::bus_stop_leg_details ORDER BY effective_time)
    AS stop_user_legs
    FROM transport_user_bus_stop_view
    WHERE bus_stop_id = bus_stop.bus_stop_id
    AND user_id = p_user_id
) stop_leg_details ON TRUE
WHERE bus_stop.atco_code = p_atco;
$$;

CREATE OR REPLACE FUNCTION select_bus_stop_user_details_by_user_id (
    p_user_id INTEGER_NOTNULL
)
RETURNS SETOF bus_stop_user_summary
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
        bus_stop_id,
        COUNT(*) AS total,
        COUNT(
            CASE
            WHEN bus_call_id = board_call_id
            THEN 1
            END
        ) AS boards,
        COUNT(
            CASE
            WHEN bus_call_id = alight_call_id
            THEN 1
            END
        ) AS alights
    FROM transport_user_bus_stop_view
    WHERE user_id = p_user_id
    GROUP BY bus_stop_id
) stop_counts
ON bus_stop.bus_stop_id = stop_counts.bus_stop_id
ORDER BY
    bus_stop.stop_name,
    bus_stop.locality_name,
    bus_stop.indicator;
$$;
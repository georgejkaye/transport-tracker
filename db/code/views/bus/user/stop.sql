DROP VIEW IF EXISTS transport_user_bus_stop_leg_view CASCADE;

CREATE VIEW transport_user_bus_stop_leg_view AS
WITH leg_stop_call AS (
    SELECT
        bus_leg.bus_leg_id,
        bus_stop.bus_stop_id,
        bus_stop.atco_code,
        bus_stop.stop_name,
        bus_stop.locality_name,
        bus_stop.street_name,
        bus_stop.indicator,
        bus_call.bus_call_id,
        bus_call.plan_arr,
        bus_call.act_arr,
        bus_call.plan_dep,
        bus_call.act_dep,
        bus_journey.bus_journey_id,
        bus_leg_summary_view.operator AS operator,
        bus_leg_summary_view.services AS services,
        bus_leg_summary_view.board_stop AS board_stop,
        bus_leg_summary_view.alight_stop AS alight_stop,
        COALESCE(
            bus_call.act_dep,
            bus_call.act_arr,
            bus_call.plan_dep,
            bus_call.plan_arr
        ) AS effective_time
    FROM bus_stop
    INNER JOIN bus_call
    ON bus_stop.bus_stop_id = bus_call.bus_stop_id
    INNER JOIN bus_journey
    ON bus_call.bus_journey_id = bus_journey.bus_journey_id
    INNER JOIN bus_leg_journey
    ON bus_journey.bus_journey_id = bus_leg_journey.bus_journey_id
    INNER JOIN bus_leg
    ON bus_leg_journey.bus_leg_id = bus_leg.bus_leg_id
    INNER JOIN bus_leg_summary_view
    ON bus_leg.bus_leg_id = bus_leg_summary_view.bus_leg_id
    INNER JOIN bus_call board_call
    ON bus_leg_journey.start_call_id = board_call.bus_call_id
    INNER JOIN bus_stop board_stop
    ON board_call.bus_stop_id = board_stop.bus_stop_id
    INNER JOIN bus_call alight_call
    ON bus_leg_journey.end_call_id = alight_call.bus_call_id
    INNER JOIN bus_stop alight_stop
    ON alight_call.bus_stop_id = alight_stop.bus_stop_id
    WHERE COALESCE(
            bus_call.act_dep,
            bus_call.act_arr,
            bus_call.plan_dep,
            bus_call.plan_arr
        ) >= COALESCE(
            (bus_leg_summary_view.board_stop).act_dep,
            (bus_leg_summary_view.board_stop).plan_dep
        )
    AND COALESCE(
            bus_call.act_arr,
            bus_call.act_dep,
            bus_call.plan_arr,
            bus_call.plan_dep
        ) <= COALESCE(
            (bus_leg_summary_view.alight_stop).act_arr,
            (bus_leg_summary_view.alight_stop).plan_arr
        )
),
ranked_leg_stop_call AS (
    SELECT
        bus_leg_id,
        bus_stop_id,
        bus_call_id,
        bus_journey_id,
        atco_code,
        stop_name,
        locality_name,
        street_name,
        indicator,
        plan_arr,
        act_arr,
        plan_dep,
        act_dep,
        operator,
        services,
        board_stop,
        alight_stop,
        effective_time,
        ROW_NUMBER() OVER (
            PARTITION BY bus_leg_id
            ORDER BY effective_time ASC NULLS LAST, bus_call_id ASC
        ) AS call_position,
        COUNT(*) OVER (
            PARTITION BY bus_leg_id
        ) AS journey_call_count
    FROM leg_stop_call
)
SELECT
    transport_user_bus_leg.user_id,
    ranked_leg_stop_call.bus_leg_id,
    ranked_leg_stop_call.bus_stop_id,
    ranked_leg_stop_call.bus_call_id,
    ranked_leg_stop_call.bus_journey_id,
    ranked_leg_stop_call.atco_code,
    ranked_leg_stop_call.stop_name,
    ranked_leg_stop_call.locality_name,
    ranked_leg_stop_call.street_name,
    ranked_leg_stop_call.indicator,
    ranked_leg_stop_call.plan_arr,
    ranked_leg_stop_call.act_arr,
    ranked_leg_stop_call.plan_dep,
    ranked_leg_stop_call.act_dep,
    ranked_leg_stop_call.operator,
    ranked_leg_stop_call.services,
    ranked_leg_stop_call.board_stop,
    ranked_leg_stop_call.alight_stop,
    ranked_leg_stop_call.effective_time,
    ranked_leg_stop_call.call_position,
    ranked_leg_stop_call.journey_call_count,
    (call_position - 1)::INT AS stops_before,
    (journey_call_count - call_position)::INT AS stops_after
FROM ranked_leg_stop_call
INNER JOIN transport_user_bus_leg
ON transport_user_bus_leg.bus_leg_id = ranked_leg_stop_call.bus_leg_id;

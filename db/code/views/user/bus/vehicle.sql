DROP VIEW IF EXISTS transport_user_bus_vehicle_view CASCADE;

CREATE OR REPLACE VIEW transport_user_bus_vehicle_view AS
SELECT
    bus_vehicle_leg_user_details.user_id AS user_id,
    bus_vehicle.bus_vehicle_id AS vehicle_id,
    bus_vehicle.vehicle_identifier AS vehicle_number,
    bus_vehicle.vehicle_name AS vehicle_name,
    bus_vehicle.numberplate AS vehicle_numberplate,
    (
        bus_operator.bus_operator_id,
        bus_operator.operator_name,
        bus_operator.national_operator_code
    )::bus_operator_summary AS vehicle_operator,
    bus_vehicle_leg_user_details.vehicle_legs,
    bus_vehicle_leg_user_details.vehicle_duration
FROM bus_vehicle
INNER JOIN bus_operator
ON bus_operator.bus_operator_id = bus_vehicle.bus_operator_id
INNER JOIN (
    SELECT
        bus_journey.bus_vehicle_id,
        transport_user_bus_leg.user_id,
        ARRAY_AGG((
            leg_journey.bus_leg_id,
            leg_journey_summary.operator,
            leg_journey_summary.journeys,
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
            COALESCE(
                alight_call.act_arr,
                alight_call.act_dep,
                alight_call.plan_arr,
                alight_call.plan_dep
            ) - COALESCE(
                board_call.act_dep,
                board_call.act_arr,
                board_call.plan_dep,
                board_call.plan_arr
            )
        )::bus_vehicle_leg_details ORDER BY COALESCE(
            board_call.act_dep,
            board_call.act_arr,
            board_call.plan_dep,
            board_call.plan_arr
        )) AS vehicle_legs,
        SUM(
            COALESCE(
                alight_call.act_arr,
                alight_call.act_dep,
                alight_call.plan_arr,
                alight_call.plan_dep
            ) - COALESCE(
                board_call.act_dep,
                board_call.act_arr,
                board_call.plan_dep,
                board_call.plan_arr
            )
        ) AS vehicle_duration
    FROM transport_user_bus_leg
        INNER JOIN bus_leg_journey_summary_view leg_journey_summary
        ON transport_user_bus_leg.bus_leg_id = leg_journey_summary.bus_leg_id
    INNER JOIN (
        SELECT DISTINCT ON (bus_leg_journey.bus_leg_id)
            bus_leg_journey.bus_leg_id,
            bus_leg_journey.bus_journey_id,
            bus_leg_journey.start_call_id,
            bus_leg_journey.end_call_id
        FROM bus_leg_journey
        INNER JOIN bus_call board_call
        ON bus_leg_journey.start_call_id = board_call.bus_call_id
        ORDER BY
            bus_leg_journey.bus_leg_id,
            COALESCE(
                board_call.plan_dep,
                board_call.plan_arr,
                board_call.act_dep,
                board_call.act_arr
            ) ASC NULLS LAST,
            bus_leg_journey.bus_leg_journey_id ASC
    ) leg_journey
    ON transport_user_bus_leg.bus_leg_id = leg_journey.bus_leg_id
    INNER JOIN bus_journey
    ON leg_journey.bus_journey_id = bus_journey.bus_journey_id
    INNER JOIN bus_call board_call
    ON leg_journey.start_call_id = board_call.bus_call_id
    INNER JOIN bus_stop board_stop
    ON board_call.bus_stop_id = board_stop.bus_stop_id
    INNER JOIN bus_call alight_call
    ON leg_journey.end_call_id = alight_call.bus_call_id
    INNER JOIN bus_stop alight_stop
    ON alight_call.bus_stop_id = alight_stop.bus_stop_id
    GROUP BY (bus_journey.bus_vehicle_id, transport_user_bus_leg.user_id)
) bus_vehicle_leg_user_details
ON bus_vehicle_leg_user_details.bus_vehicle_id = bus_vehicle.bus_vehicle_id;
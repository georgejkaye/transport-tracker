DROP VIEW IF EXISTS transport_user_bus_leg_details_view CASCADE;

CREATE VIEW transport_user_bus_leg_details_view AS
SELECT
    transport_user_bus_leg.bus_leg_id AS leg_id,
    transport_user_bus_leg.user_id,
    leg_journey_summary.operator AS operator,
    leg_journey_summary.journeys AS journeys,
    CASE
        WHEN bus_vehicle.bus_vehicle_id IS NULL THEN NULL
        ELSE (
            bus_vehicle.bus_vehicle_id,
            (
                bus_vehicle_operator.bus_operator_id,
                bus_vehicle_operator.operator_name,
                bus_vehicle_operator.national_operator_code
            )::bus_operator_summary,
            bus_vehicle.vehicle_identifier,
            bus_vehicle.bustimes_id,
            bus_vehicle.numberplate,
            bus_model.bus_model_name,
            bus_vehicle.livery_style,
            bus_vehicle.vehicle_name
        )::bus_vehicle_details
    END AS vehicle,
    leg_call_summary.leg_calls AS calls,
    (
        ((leg_call_endpoints.start_call).stop).bus_stop_id,
        ((leg_call_endpoints.start_call).stop).stop_atco,
        ((leg_call_endpoints.start_call).stop).stop_name,
        ((leg_call_endpoints.start_call).stop).stop_locality,
        ((leg_call_endpoints.start_call).stop).stop_indicator,
        (leg_call_endpoints.start_call).plan_dep,
        (leg_call_endpoints.start_call).act_dep
    )::bus_leg_summary_board_stop AS board_stop,
    (
        ((leg_call_endpoints.end_call).stop).bus_stop_id,
        ((leg_call_endpoints.end_call).stop).stop_atco,
        ((leg_call_endpoints.end_call).stop).stop_name,
        ((leg_call_endpoints.end_call).stop).stop_locality,
        ((leg_call_endpoints.end_call).stop).stop_indicator,
        (leg_call_endpoints.end_call).plan_arr,
        (leg_call_endpoints.end_call).act_arr
    )::bus_leg_summary_alight_stop AS alight_stop,
    COALESCE(
        (leg_call_endpoints.end_call).act_arr,
        (leg_call_endpoints.end_call).plan_arr,
        (leg_call_endpoints.end_call).act_dep,
        (leg_call_endpoints.end_call).plan_dep
    ) - COALESCE(
            (leg_call_endpoints.start_call).act_arr,
            (leg_call_endpoints.start_call).plan_arr,
            (leg_call_endpoints.start_call).act_dep,
            (leg_call_endpoints.start_call).plan_dep
    ) AS duration
FROM transport_user_bus_leg
INNER JOIN bus_leg_journey_summary_view leg_journey_summary
ON transport_user_bus_leg.bus_leg_id = leg_journey_summary.bus_leg_id
INNER JOIN (
    SELECT DISTINCT ON (bus_leg_journey.bus_leg_id)
        bus_leg_journey.bus_leg_id,
        bus_leg_journey.bus_journey_id
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
LEFT JOIN bus_vehicle
ON bus_journey.bus_vehicle_id = bus_vehicle.bus_vehicle_id
LEFT JOIN bus_operator bus_vehicle_operator
ON bus_vehicle.bus_operator_id = bus_vehicle_operator.bus_operator_id
LEFT JOIN bus_model
ON bus_vehicle.bus_model_id = bus_model.bus_model_id
INNER JOIN (
    SELECT
        bus_leg_journey.bus_leg_id,
        ARRAY_AGG (
            (
                bus_call.bus_call_id,
                (
                    bus_stop.bus_stop_id,
                    bus_stop.atco_code,
                    bus_stop.stop_name,
                    bus_stop.locality_name,
                    bus_stop.street_name,
                    bus_stop.indicator
                )::bus_call_stop_details,
                bus_call.plan_arr,
                bus_call.act_arr,
                bus_call.plan_dep,
                bus_call.act_dep
            )::bus_call_details
            ORDER BY
                COALESCE(
                    bus_call.plan_dep,
                    bus_call.plan_arr,
                    bus_call.act_dep,
                    bus_call.act_arr
                ),
                bus_call.bus_call_id
        ) AS leg_calls
    FROM bus_leg_journey
    INNER JOIN bus_call start_call
    ON bus_leg_journey.start_call_id = start_call.bus_call_id
    INNER JOIN bus_call end_call
    ON bus_leg_journey.end_call_id = end_call.bus_call_id
    INNER JOIN bus_call
    ON bus_call.bus_journey_id = bus_leg_journey.bus_journey_id
    AND bus_call.call_index >= start_call.call_index
    AND bus_call.call_index <= end_call.call_index
    INNER JOIN bus_stop
    ON bus_call.bus_stop_id = bus_stop.bus_stop_id
    GROUP BY bus_leg_journey.bus_leg_id
) leg_call_summary
ON transport_user_bus_leg.bus_leg_id = leg_call_summary.bus_leg_id
CROSS JOIN LATERAL (
    SELECT
        leg_call_summary.leg_calls[1] AS start_call,
        leg_call_summary.leg_calls[
            array_upper(leg_call_summary.leg_calls, 1)
        ] AS end_call
) leg_call_endpoints;
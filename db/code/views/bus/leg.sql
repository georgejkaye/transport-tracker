DROP VIEW IF EXISTS bus_leg_summary_view CASCADE;
DROP VIEW IF EXISTS bus_leg_journey_summary_view CASCADE;

CREATE VIEW bus_leg_summary_view AS
SELECT
    bus_leg.bus_leg_id,
    (
        bus_leg_operator.bus_operator_id,
        bus_leg_operator.operator_name,
        bus_leg_operator.national_operator_code
    )::bus_operator_summary AS operator,
    bus_leg_service.services,
    CASE
        WHEN bus_leg_vehicle.bus_vehicle_id IS NULL THEN NULL
        ELSE (
            bus_leg_vehicle.bus_vehicle_id,
            bus_leg_vehicle.operator,
            bus_leg_vehicle.vehicle_identifier,
            bus_leg_vehicle.numberplate,
            bus_leg_vehicle.vehicle_name
        )::bus_vehicle_summary
    END AS vehicle,
    (
        bus_leg_board.bus_stop_id,
        bus_leg_board.atco_code,
        bus_leg_board.stop_name,
        bus_leg_board.locality_name,
        bus_leg_board.indicator,
        COALESCE(bus_leg_board.plan_dep, bus_leg_board.plan_arr),
        COALESCE(bus_leg_board.act_dep, bus_leg_board.act_arr)
    )::bus_leg_summary_board_stop AS board_stop,
    (
        bus_leg_alight.bus_stop_id,
        bus_leg_alight.atco_code,
        bus_leg_alight.stop_name,
        bus_leg_alight.locality_name,
        bus_leg_alight.indicator,
        COALESCE(bus_leg_alight.plan_dep, bus_leg_alight.plan_arr),
        COALESCE(bus_leg_alight.act_dep, bus_leg_alight.act_arr)
    )::bus_leg_summary_alight_stop AS alight_stop,
    COALESCE(bus_leg_alight.act_arr, bus_leg_alight.act_dep,
        bus_leg_alight.plan_arr, bus_leg_alight.plan_dep)
    - COALESCE(bus_leg_board.act_dep, bus_leg_board.act_arr,
        bus_leg_board.plan_dep, bus_leg_board.plan_arr)
        AS duration
FROM bus_leg
INNER JOIN (
    SELECT DISTINCT
        bus_leg.bus_leg_id,
        ARRAY_AGG(
            (
                bus_service.bus_service_id,
                (
                    bus_operator.bus_operator_id,
                    bus_operator.operator_name,
                    bus_operator.national_operator_code
                )::bus_operator_summary,
                bus_service.service_line
            )::bus_service_summary
        ) AS services
    FROM bus_leg
    INNER JOIN bus_leg_journey
    ON bus_leg.bus_leg_id = bus_leg_journey.bus_leg_id
    INNER JOIN bus_journey
    ON bus_leg_journey.bus_journey_id = bus_journey.bus_journey_id
    INNER JOIN bus_service
    ON bus_journey.bus_service_id = bus_service.bus_service_id
    INNER JOIN bus_operator
    ON bus_service.bus_operator_id = bus_operator.bus_operator_id
    GROUP BY bus_leg.bus_leg_id
) bus_leg_service
ON bus_leg.bus_leg_id = bus_leg_service.bus_leg_id
INNER JOIN (
    SELECT DISTINCT ON (bus_leg_journey.bus_leg_id)
        bus_leg_journey.bus_leg_id,
        board_stop.bus_stop_id,
        board_stop.atco_code,
        board_stop.locality_name,
        board_stop.stop_name,
        board_stop.street_name,
        board_stop.indicator,
        board_call.plan_dep,
        board_call.act_dep,
        board_call.plan_arr,
        board_call.act_arr
    FROM bus_leg_journey
    INNER JOIN bus_call board_call
    ON bus_leg_journey.start_call_id = board_call.bus_call_id
    INNER JOIN bus_stop board_stop
    ON board_call.bus_stop_id = board_stop.bus_stop_id
    ORDER BY
        bus_leg_journey.bus_leg_id,
        COALESCE(
            board_call.plan_dep,
            board_call.plan_arr
        ) ASC NULLS LAST,
        board_call.bus_call_id ASC
) bus_leg_board
ON bus_leg.bus_leg_id = bus_leg_board.bus_leg_id
INNER JOIN (
    SELECT DISTINCT ON (bus_leg_journey.bus_leg_id)
        bus_leg_journey.bus_leg_id,
        alight_stop.bus_stop_id,
        alight_stop.atco_code,
        alight_stop.locality_name,
        alight_stop.stop_name,
        alight_stop.street_name,
        alight_stop.indicator,
        alight_call.plan_dep,
        alight_call.act_dep,
        alight_call.plan_arr,
        alight_call.act_arr
    FROM bus_leg_journey
    INNER JOIN bus_call alight_call
    ON bus_leg_journey.end_call_id = alight_call.bus_call_id
    INNER JOIN bus_stop alight_stop
    ON alight_call.bus_stop_id = alight_stop.bus_stop_id
    ORDER BY
        bus_leg_journey.bus_leg_id,
        COALESCE(
            alight_call.plan_arr,
            alight_call.plan_dep
        ) DESC NULLS LAST,
        alight_call.bus_call_id DESC
) bus_leg_alight
ON bus_leg.bus_leg_id = bus_leg_alight.bus_leg_id
INNER JOIN (
    SELECT DISTINCT
        bus_leg.bus_leg_id,
        bus_operator.bus_operator_id,
        bus_operator.operator_name,
        bus_operator.national_operator_code
    FROM bus_leg
    INNER JOIN bus_leg_journey
    ON bus_leg.bus_leg_id = bus_leg_journey.bus_leg_id
    INNER JOIN bus_journey
    ON bus_leg_journey.bus_journey_id = bus_journey.bus_journey_id
    INNER JOIN bus_service
    ON bus_journey.bus_service_id = bus_service.bus_service_id
    INNER JOIN bus_operator
    ON bus_service.bus_operator_id = bus_operator.bus_operator_id
) bus_leg_operator
ON bus_leg.bus_leg_id = bus_leg_operator.bus_leg_id
LEFT JOIN (
    SELECT DISTINCT
        bus_leg.bus_leg_id,
        (
            bus_operator.bus_operator_id,
            bus_operator.operator_name,
            bus_operator.national_operator_code
        )::bus_operator_summary AS operator,
        bus_vehicle.bus_vehicle_id,
        bus_vehicle.vehicle_identifier,
        bus_vehicle.numberplate,
        bus_vehicle.vehicle_name
    FROM bus_leg
    INNER JOIN bus_leg_journey
    ON bus_leg.bus_leg_id = bus_leg_journey.bus_leg_id
    INNER JOIN bus_journey
    ON bus_leg_journey.bus_journey_id = bus_journey.bus_journey_id
    INNER JOIN bus_vehicle
    ON bus_journey.bus_vehicle_id = bus_vehicle.bus_vehicle_id
    INNER JOIN bus_operator
    ON bus_vehicle.bus_operator_id = bus_operator.bus_operator_id
) bus_leg_vehicle
ON bus_leg.bus_leg_id = bus_leg_vehicle.bus_leg_id;

CREATE VIEW bus_leg_journey_summary_view AS
SELECT
    bus_leg_journey.bus_leg_id,
    ARRAY_AGG((
        bus_journey.bus_journey_id,
        bus_service.bus_service_id,
        bus_service.service_line,
        (
            journey_start.bus_stop_id,
            journey_start.stop_name,
            journey_start.locality_name,
            journey_start.indicator
        )::bus_leg_journey_stop_summary,
        (
            journey_end.bus_stop_id,
            journey_end.stop_name,
            journey_end.locality_name,
            journey_end.indicator
        )::bus_leg_journey_stop_summary,
        (
            leg_start.bus_stop_id,
            leg_start.stop_name,
            leg_start.locality_name,
            leg_start.indicator
        )::bus_leg_journey_stop_summary,
        (
            leg_end.bus_stop_id,
            leg_end.stop_name,
            leg_end.locality_name,
            leg_end.indicator
        )::bus_leg_journey_stop_summary
    )::bus_leg_journey_summary ORDER BY COALESCE(
        leg_start_call.plan_dep,
        leg_start_call.plan_arr,
        leg_start_call.act_dep,
        leg_start_call.act_arr
    ) ASC NULLS LAST, bus_leg_journey.bus_leg_journey_id) AS journeys,
    (ARRAY_AGG((
        bus_operator.bus_operator_id,
        bus_operator.operator_name,
        bus_operator.national_operator_code
    )::bus_operator_summary ORDER BY COALESCE(
        leg_start_call.plan_dep,
        leg_start_call.plan_arr,
        leg_start_call.act_dep,
        leg_start_call.act_arr
    ) ASC NULLS LAST, bus_leg_journey.bus_leg_journey_id))[1]
        AS operator
FROM bus_leg_journey
INNER JOIN bus_journey
ON bus_leg_journey.bus_journey_id = bus_journey.bus_journey_id
INNER JOIN bus_service
ON bus_journey.bus_service_id = bus_service.bus_service_id
INNER JOIN bus_operator
ON bus_service.bus_operator_id = bus_operator.bus_operator_id
INNER JOIN bus_call leg_start_call
ON bus_leg_journey.start_call_id = leg_start_call.bus_call_id
INNER JOIN bus_stop leg_start
ON leg_start_call.bus_stop_id = leg_start.bus_stop_id
INNER JOIN bus_call leg_end_call
ON bus_leg_journey.end_call_id = leg_end_call.bus_call_id
INNER JOIN bus_stop leg_end
ON leg_end_call.bus_stop_id = leg_end.bus_stop_id
INNER JOIN LATERAL (
    SELECT
        journey_start_call.bus_stop_id,
        journey_start.stop_name,
        journey_start.locality_name,
        journey_start.indicator
    FROM bus_call journey_start_call
    INNER JOIN bus_stop journey_start
    ON journey_start_call.bus_stop_id = journey_start.bus_stop_id
    WHERE journey_start_call.bus_journey_id = bus_journey.bus_journey_id
    ORDER BY
        journey_start_call.call_index ASC,
        journey_start_call.bus_call_id ASC
    LIMIT 1
) journey_start ON TRUE
INNER JOIN LATERAL (
    SELECT
        journey_end_call.bus_stop_id,
        journey_end.stop_name,
        journey_end.locality_name,
        journey_end.indicator
    FROM bus_call journey_end_call
    INNER JOIN bus_stop journey_end
    ON journey_end_call.bus_stop_id = journey_end.bus_stop_id
    WHERE journey_end_call.bus_journey_id = bus_journey.bus_journey_id
    ORDER BY
        journey_end_call.call_index DESC,
        journey_end_call.bus_call_id DESC
    LIMIT 1
) journey_end ON TRUE
GROUP BY bus_leg_journey.bus_leg_id;

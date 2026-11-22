DROP VIEW IF EXISTS bus_leg_summary_view CASCADE;

CREATE VIEW bus_leg_summary_view AS
SELECT
    bus_leg.bus_leg_id,
    bus_leg_board.bus_stop_id AS board_stop_id,
    bus_leg_board.atco_code AS board_atco_code,
    bus_leg_board.locality_name AS board_locality_name,
    bus_leg_board.stop_name AS board_stop_name,
    bus_leg_board.street_name AS board_street_name,
    bus_leg_board.indicator AS board_indicator,
    COALESCE(bus_leg_board.plan_dep, bus_leg_board.plan_arr)
        AS plan_board_time,
    COALESCE(bus_leg_board.act_dep, bus_leg_board.act_arr)
        AS act_board_time,
    bus_leg_alight.bus_stop_id AS alight_stop_id,
    bus_leg_alight.atco_code AS alight_atco_code,
    bus_leg_alight.locality_name AS alight_locality_name,
    bus_leg_alight.stop_name AS alight_stop_name,
    bus_leg_alight.street_name AS alight_street_name,
    bus_leg_alight.indicator AS alight_indicator,
    COALESCE(bus_leg_alight.plan_dep, bus_leg_alight.plan_arr)
        AS plan_alight_time,
    COALESCE(bus_leg_alight.act_dep, bus_leg_alight.act_arr)
        AS act_alight_time,
    COALESCE(bus_leg_alight.act_arr, bus_leg_alight.act_dep,
        bus_leg_alight.plan_arr, bus_leg_alight.plan_dep)
    - COALESCE(bus_leg_board.act_dep, bus_leg_board.act_arr,
        bus_leg_board.plan_dep, bus_leg_board.plan_arr)
        AS duration,
    bus_leg_operator.bus_operator_id,
    bus_leg_operator.operator_name,
    bus_leg_vehicle.bus_vehicle_id,
    bus_leg_vehicle.vehicle_identifier,
    bus_leg_vehicle.numberplate
FROM bus_leg
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
        bus_operator.operator_name
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
        bus_vehicle.bus_vehicle_id,
        bus_vehicle.vehicle_identifier,
        bus_vehicle.numberplate
    FROM bus_leg
    INNER JOIN bus_leg_journey
    ON bus_leg.bus_leg_id = bus_leg_journey.bus_leg_id
    INNER JOIN bus_journey
    ON bus_leg_journey.bus_journey_id = bus_journey.bus_journey_id
    INNER JOIN bus_vehicle
    ON bus_journey.bus_vehicle_id = bus_vehicle.bus_vehicle_id
) bus_leg_vehicle
ON bus_leg.bus_leg_id = bus_leg_vehicle.bus_leg_id;

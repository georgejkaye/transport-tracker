CREATE OR REPLACE VIEW bus_stop_leg_details_view AS
SELECT
    bus_stop.bus_stop_id,
    transport_user_bus_leg.user_id,
    ARRAY_AGG(
        (
            bus_leg.bus_leg_id,
            (
                bus_service.bus_service_id,
                bus_service.service_line,
                (
                    bus_operator.bus_operator_id,
                    bus_operator.operator_name,
                    bus_operator.national_operator_code,
                    bus_operator.bg_colour,
                    bus_operator.fg_colour
                )::bus_operator_details,
                bus_service.description_outbound,
                bus_service.description_inbound,
                bus_service.bg_colour,
                bus_service.fg_colour
            )::bus_leg_service_details,
            (
                BoardCall.bus_call_id,
                BoardCall.call_index,
                (
                    BoardStop.bus_stop_id,
                    BoardStop.atco_code,
                    BoardStop.stop_name,
                    BoardStop.locality_name,
                    BoardStop.street_name,
                    BoardStop.indicator
                )::bus_call_stop_details,
                BoardCall.plan_arr,
                BoardCall.act_arr,
                BoardCall.plan_dep,
                BoardCall.act_dep
            )::bus_call_details,
            (
                AlightCall.bus_call_id,
                AlightCall.call_index,
                (
                    AlightStop.bus_stop_id,
                    AlightStop.atco_code,
                    AlightStop.stop_name,
                    AlightStop.locality_name,
                    AlightStop.street_name,
                    AlightStop.indicator
                )::bus_call_stop_details,
                AlightCall.plan_arr,
                AlightCall.act_arr,
                AlightCall.plan_dep,
                AlightCall.act_dep
            )::bus_call_details,
            (
                bus_call.bus_call_id,
                bus_call.call_index,
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
            )::bus_call_details,
            (bus_call.call_index - BoardCall.call_index),
            (AlightCall.call_index - bus_call.call_index)
        )::bus_stop_leg_details
        ORDER BY
            COALESCE(
                bus_call.act_dep,
                bus_call.act_arr,
                bus_call.plan_dep,
                bus_call.plan_arr
            )
    ) AS stop_user_legs
FROM bus_stop
INNER JOIN bus_call
ON bus_stop.bus_stop_id = bus_call.bus_stop_id
INNER JOIN bus_journey
ON bus_call.bus_journey_id = bus_journey.bus_journey_id
INNER JOIN bus_leg
ON bus_journey.bus_journey_id = bus_leg.bus_journey_id
INNER JOIN bus_service
ON bus_journey.bus_service_id = bus_service.bus_service_id
INNER JOIN bus_operator
ON bus_service.bus_operator_id = bus_operator.bus_operator_id
INNER JOIN bus_call BoardCall
ON bus_leg.board_call_index = BoardCall.call_index
AND bus_journey.bus_journey_id = BoardCall.bus_journey_id
INNER JOIN bus_stop BoardStop
ON BoardCall.bus_stop_id = BoardStop.bus_stop_id
INNER JOIN bus_call AlightCall
ON bus_leg.alight_call_index = AlightCall.call_index
AND bus_journey.bus_journey_id = AlightCall.bus_journey_id
INNER JOIN bus_stop AlightStop
ON AlightCall.bus_stop_id = AlightStop.bus_stop_id
INNER JOIN transport_user_bus_leg
ON bus_leg.bus_leg_id = transport_user_bus_leg.bus_leg_id
WHERE bus_call.call_index >= BoardCall.call_index
AND bus_call.call_index <= AlightCall.call_index
GROUP BY bus_stop.bus_stop_id, transport_user_bus_leg.user_id;

CREATE OR REPLACE VIEW bus_leg_user_details_view AS
SELECT
    bus_leg.bus_leg_id AS leg_id,
    transport_user_bus_leg.user_id,
    (
        bus_service.bus_service_id,
        bus_service.service_line,
        (
            bus_operator.bus_operator_id,
            bus_operator.operator_name,
            bus_operator.national_operator_code,
            bus_operator.bg_colour,
            bus_operator.fg_colour
        )::bus_operator_details,
        bus_service.description_outbound,
        bus_service.description_inbound,
        bus_service.bg_colour,
        bus_service.fg_colour
    )::bus_leg_service_details AS leg_service,
    (
        bus_vehicle.bus_vehicle_id,
        (
            BusVehicleOperator.bus_operator_id,
            BusVehicleOperator.operator_name,
            BusVehicleOperator.national_operator_code,
            BusVehicleOperator.bg_colour,
            BusVehicleOperator.fg_colour
        )::bus_operator_details,
        bus_vehicle.vehicle_identifier,
        bus_vehicle.bustimes_id,
        bus_vehicle.numberplate,
        bus_model.bus_model_name,
        bus_vehicle.livery_style,
        bus_vehicle.vehicle_name
    )::bus_vehicle_details AS leg_vehicle,
    BusLegCall.leg_calls AS leg_calls,
    COALESCE(
        BusLegCall.leg_calls[array_upper(BusLegCall.leg_calls, 1)].act_arr,
        BusLegCall.leg_calls[array_upper(BusLegCall.leg_calls, 1)].plan_arr,
        BusLegCall.leg_calls[array_upper(BusLegCall.leg_calls, 1)].act_dep,
        BusLegCall.leg_calls[array_upper(BusLegCall.leg_calls, 1)].plan_dep
    ) - COALESCE(
            BusLegCall.leg_calls[1].act_arr,
            BusLegCall.leg_calls[1].plan_arr,
            BusLegCall.leg_calls[1].act_dep,
            BusLegCall.leg_calls[1].plan_dep
    ) AS leg_duration
FROM transport_user_bus_leg
INNER JOIN bus_leg
ON transport_user_bus_leg.bus_leg_id = bus_leg.bus_leg_id
INNER JOIN bus_journey
ON bus_leg.bus_journey_id = bus_journey.bus_journey_id
INNER JOIN bus_service
ON bus_journey.bus_service_id = bus_service.bus_service_id
INNER JOIN bus_operator
ON bus_service.bus_operator_id = bus_operator.bus_operator_id
INNER JOIN bus_vehicle
ON bus_journey.bus_vehicle_id = bus_vehicle.bus_vehicle_id
INNER JOIN bus_operator BusVehicleOperator
ON bus_vehicle.bus_operator_id = BusVehicleOperator.bus_operator_id
INNER JOIN bus_model
ON bus_vehicle.bus_model_id = bus_model.bus_model_id
INNER JOIN (
    SELECT
        bus_leg.bus_leg_id,
        ARRAY_AGG (
            (
                bus_call.bus_call_id,
                bus_call.call_index,
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
            ORDER BY bus_call.call_index
        ) AS leg_calls
    FROM bus_leg
    INNER JOIN bus_journey
    ON bus_leg.bus_journey_id = bus_journey.bus_journey_id
    INNER JOIN bus_call
    ON bus_journey.bus_journey_id = bus_call.bus_journey_id
    INNER JOIN bus_stop
    ON bus_call.bus_stop_id = bus_stop.bus_stop_id
    WHERE bus_call.call_index >= bus_leg.board_call_index
    AND bus_call.call_index <= bus_leg.alight_call_index
    GROUP BY bus_leg.bus_leg_id
) BusLegCall
ON bus_leg.bus_leg_id = BusLegCall.bus_leg_id;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details(
    p_user_id INTEGER_NOTNULL
)
RETURNS SETOF bus_leg_user_details
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        bus_leg_user_details_view.leg_id,
        bus_leg_user_details_view.leg_service,
        bus_leg_user_details_view.leg_vehicle,
        bus_leg_user_details_view.leg_calls,
        bus_leg_user_details_view.leg_duration
    FROM bus_leg_user_details_view
    WHERE bus_leg_user_details_view.user_id = p_user_id
    ORDER BY COALESCE(
        (bus_leg_user_details_view.leg_calls)[1].act_dep,
        (bus_leg_user_details_view.leg_calls)[1].plan_dep,
        (bus_leg_user_details_view.leg_calls)[1].act_arr,
        (bus_leg_user_details_view.leg_calls)[1].plan_arr);
END;
$$;

CREATE OR REPLACE VIEW bus_service_details_view AS
SELECT
    bus_service.bus_service_id,
    (
        bus_operator.bus_operator_id,
        bus_operator.operator_name,
        bus_operator.national_operator_code,
        bus_operator.bg_colour,
        bus_operator.fg_colour
    )::bus_operator_details AS service_operator,
    bus_service.service_line,
    bus_service.description_outbound,
    OutboundVia.service_vias AS service_outbound_vias,
    bus_service.description_inbound,
    InboundVia.service_vias AS service_inbound_vias,
    bus_service.bg_colour,
    bus_service.fg_colour
FROM bus_service
LEFT JOIN (
    SELECT
        bus_service_id,
        ARRAY_AGG(
            bus_service_via.via_name
            ORDER BY bus_service_via.via_index
        ) AS service_vias
    FROM bus_service_via
    WHERE is_outbound = 'true'
    GROUP BY
        bus_service_via.bus_service_id,
        bus_service_via.is_outbound
) OutboundVia
ON bus_service.bus_service_id = OutboundVia.bus_service_id
LEFT JOIN (
    SELECT
        bus_service_id,
        ARRAY_AGG(
            bus_service_via.via_name
            ORDER BY bus_service_via.via_index
        ) AS service_vias
    FROM bus_service_via
    WHERE is_outbound = 'false'
    GROUP BY
        bus_service_via.bus_service_id,
        bus_service_via.is_outbound
) InboundVia
ON bus_service.bus_service_id = InboundVia.bus_service_id
INNER JOIN bus_operator
ON bus_operator.bus_operator_id = bus_service.bus_operator_id;

CREATE OR REPLACE VIEW bus_vehicle_data AS
SELECT
    bus_vehicle.bus_vehicle_id,
    (
        bus_operator.bus_operator_id,
        bus_operator.operator_name,
        bus_operator.national_operator_code,
        bus_operator.bg_colour,
        bus_operator.fg_colour
    )::bus_operator_details AS vehicle_operator,
    bus_vehicle.vehicle_identifier,
    bus_vehicle.bustimes_id,
    bus_vehicle.numberplate,
    bus_model.bus_model_name,
    bus_vehicle.livery_style,
    bus_vehicle.vehicle_name
FROM bus_vehicle
INNER JOIN bus_operator
ON bus_vehicle.bus_operator_id = bus_operator.bus_operator_id
INNER JOIN bus_model
ON bus_model.bus_model_id = bus_vehicle.bus_model_id;

CREATE OR REPLACE VIEW bus_vehicle_user_details_view AS
SELECT
    BusVehicleLegUserDetails.user_id AS user_id,
    bus_vehicle.bus_vehicle_id AS vehicle_id,
    bus_vehicle.vehicle_identifier AS vehicle_number,
    bus_vehicle.vehicle_name AS vehicle_name,
    bus_vehicle.numberplate AS vehicle_numberplate,
    BusOperatorOut.operator_out AS vehicle_operator,
    BusVehicleLegUserDetails.vehicle_legs,
    BusVehicleLegUserDetails.vehicle_duration
FROM bus_vehicle
INNER JOIN (
    SELECT (
        bus_operator_id,
        operator_name,
        national_operator_code,
        bg_colour,
        fg_colour)::bus_operator_details AS operator_out
    FROM bus_operator
) BusOperatorOut
ON (BusOperatorOut.operator_out).bus_operator_id = bus_vehicle.bus_operator_id
INNER JOIN (
    SELECT
        bus_journey.bus_vehicle_id,
        transport_user_bus_leg.user_id,
        ARRAY_AGG(
            (
                bus_leg.bus_leg_id,
                (
                    bus_service.bus_service_id,
                    bus_service.service_line,
                    (
                        bus_operator.bus_operator_id,
                        bus_operator.operator_name,
                        bus_operator.national_operator_code,
                        bus_operator.bg_colour,
                        bus_operator.fg_colour
                    )::bus_operator_details,
                    bus_service.description_outbound,
                    bus_service.description_inbound,
                    bus_service.bg_colour,
                    bus_service.fg_colour
                )::bus_leg_service_details,
                BusJourneyCallDetail.bus_journey_call[bus_leg.board_call_index + 1],
                BusJourneyCallDetail.bus_journey_call[bus_leg.alight_call_index + 1],
                COALESCE(
                    (BusJourneyCallDetail.bus_journey_call[bus_leg.alight_call_index + 1]).act_arr,
                    (BusJourneyCallDetail.bus_journey_call[bus_leg.alight_call_index + 1]).act_dep,
                    (BusJourneyCallDetail.bus_journey_call[bus_leg.alight_call_index + 1]).plan_arr,
                    (BusJourneyCallDetail.bus_journey_call[bus_leg.alight_call_index + 1]).plan_dep
                ) -
                COALESCE(
                    (BusJourneyCallDetail.bus_journey_call[bus_leg.board_call_index + 1]).act_dep,
                    (BusJourneyCallDetail.bus_journey_call[bus_leg.board_call_index + 1]).act_arr,
                    (BusJourneyCallDetail.bus_journey_call[bus_leg.board_call_index + 1]).plan_dep,
                    (BusJourneyCallDetail.bus_journey_call[bus_leg.board_call_index + 1]).plan_arr
                )
            )::bus_vehicle_leg_details
        ) AS vehicle_legs,
        SUM(
            COALESCE(
                (BusJourneyCallDetail.bus_journey_call[bus_leg.alight_call_index + 1]).act_arr,
                (BusJourneyCallDetail.bus_journey_call[bus_leg.alight_call_index + 1]).act_dep,
                (BusJourneyCallDetail.bus_journey_call[bus_leg.alight_call_index + 1]).plan_arr,
                (BusJourneyCallDetail.bus_journey_call[bus_leg.alight_call_index + 1]).plan_dep
            ) -
            COALESCE(
                (BusJourneyCallDetail.bus_journey_call[bus_leg.board_call_index + 1]).act_dep,
                (BusJourneyCallDetail.bus_journey_call[bus_leg.board_call_index + 1]).act_arr,
                (BusJourneyCallDetail.bus_journey_call[bus_leg.board_call_index + 1]).plan_dep,
                (BusJourneyCallDetail.bus_journey_call[bus_leg.board_call_index + 1]).plan_arr
            )
        ) AS vehicle_duration
    FROM bus_leg
    INNER JOIN transport_user_bus_leg
    ON bus_leg.bus_leg_id = transport_user_bus_leg.bus_leg_id
    INNER JOIN bus_journey
    ON bus_leg.bus_journey_id = bus_journey.bus_journey_id
    INNER JOIN bus_service
    ON bus_journey.bus_service_id = bus_service.bus_service_id
    INNER JOIN bus_operator
    ON bus_service.bus_operator_id = bus_operator.bus_operator_id
    INNER JOIN (
        SELECT
            bus_journey.bus_journey_id,
            ARRAY_AGG((
                bus_call.bus_call_id,
                bus_call.call_index,
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
            )::bus_call_details ORDER BY call_index) AS bus_journey_call
        FROM bus_call
        INNER JOIN bus_journey
        ON bus_call.bus_journey_id = bus_journey.bus_journey_id
        INNER JOIN bus_stop
        ON bus_call.bus_stop_id = bus_stop.bus_stop_id
        GROUP BY bus_journey.bus_journey_id
    ) BusJourneyCallDetail
    ON bus_journey.bus_journey_id = BusJourneyCallDetail.bus_journey_id
    GROUP BY (bus_vehicle_id, transport_user_bus_leg.user_id)
) BusVehicleLegUserDetails
ON BusVehicleLegUserDetails.bus_vehicle_id = bus_vehicle.bus_vehicle_id;

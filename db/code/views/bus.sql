CREATE OR REPLACE VIEW bus_stop_leg_details_view AS
SELECT
    BusStop.bus_stop_id,
    BusLeg.user_id,
    ARRAY_AGG(
        (
            BusLeg.bus_leg_id,
            (
                BusService.bus_service_id,
                BusService.service_line,
                (
                    BusOperator.bus_operator_id,
                    BusOperator.operator_name,
                    BusOperator.national_operator_code,
                    BusOperator.bg_colour,
                    BusOperator.fg_colour
                )::bus_operator_details,
                BusService.description_outbound,
                BusService.description_inbound,
                BusService.bg_colour,
                BusService.fg_colour
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
                BusCall.bus_call_id,
                BusCall.call_index,
                (
                    BusStop.bus_stop_id,
                    BusStop.atco_code,
                    BusStop.stop_name,
                    BusStop.locality_name,
                    BusStop.street_name,
                    BusStop.indicator
                )::bus_call_stop_details,
                BusCall.plan_arr,
                BusCall.act_arr,
                BusCall.plan_dep,
                BusCall.act_dep
            )::bus_call_details,
            (BusCall.call_index - BoardCall.call_index),
            (AlightCall.call_index - BusCall.call_index)
        )::bus_stop_leg_details
        ORDER BY
            COALESCE(
                BusCall.act_dep,
                BusCall.act_arr,
                BusCall.plan_dep,
                BusCall.plan_arr
            )
    ) AS stop_user_legs
FROM BusStop
INNER JOIN BusCall
ON BusStop.bus_stop_id = BusCall.bus_stop_id
INNER JOIN BusJourney
ON BusCall.bus_journey_id = BusJourney.bus_journey_id
INNER JOIN BusLeg
ON BusJourney.bus_journey_id = BusLeg.bus_journey_id
INNER JOIN BusService
ON BusJourney.bus_service_id = BusService.bus_service_id
INNER JOIN BusOperator
ON BusService.bus_operator_id = BusOperator.bus_operator_id
INNER JOIN BusCall BoardCall
ON BusLeg.board_call_index = BoardCall.call_index
AND BusJourney.bus_journey_id = BoardCall.bus_journey_id
INNER JOIN BusStop BoardStop
ON BoardCall.bus_stop_id = BoardStop.bus_stop_id
INNER JOIN BusCall AlightCall
ON BusLeg.alight_call_index = AlightCall.call_index
AND BusJourney.bus_journey_id = AlightCall.bus_journey_id
INNER JOIN BusStop AlightStop
ON AlightCall.bus_stop_id = AlightStop.bus_stop_id
INNER JOIN transport_user
ON BusLeg.user_id = transport_user.user_id
WHERE BusCall.call_index >= BoardCall.call_index
AND BusCall.call_index <= AlightCall.call_index
GROUP BY BusStop.bus_stop_id, BusLeg.user_id;

CREATE OR REPLACE VIEW bus_leg_user_details_view AS
SELECT
    BusLeg.bus_leg_id AS leg_id,
    BusLeg.user_id AS user_id,
    (
        BusService.bus_service_id,
        BusService.service_line,
        (
            BusOperator.bus_operator_id,
            BusOperator.operator_name,
            BusOperator.national_operator_code,
            BusOperator.bg_colour,
            BusOperator.fg_colour
        )::bus_operator_details,
        BusService.description_outbound,
        BusService.description_inbound,
        BusService.bg_colour,
        BusService.fg_colour
    )::bus_leg_service_details AS leg_service,
    (
        BusVehicle.bus_vehicle_id,
        (
            BusVehicleOperator.bus_operator_id,
            BusVehicleOperator.operator_name,
            BusVehicleOperator.national_operator_code,
            BusVehicleOperator.bg_colour,
            BusVehicleOperator.fg_colour
        )::bus_operator_details,
        BusVehicle.vehicle_identifier,
        BusVehicle.bustimes_id,
        BusVehicle.numberplate,
        BusModel.bus_model_name,
        BusVehicle.livery_style,
        BusVehicle.vehicle_name
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
FROM BusLeg
INNER JOIN BusJourney
ON BusLeg.bus_journey_id = BusJourney.bus_journey_id
INNER JOIN BusService
ON BusJourney.bus_service_id = BusService.bus_service_id
INNER JOIN BusOperator
ON BusService.bus_operator_id = BusOperator.bus_operator_id
INNER JOIN BusVehicle
ON BusJourney.bus_vehicle_id = BusVehicle.bus_vehicle_id
INNER JOIN BusOperator BusVehicleOperator
ON BusVehicle.bus_operator_id = BusVehicleOperator.bus_operator_id
INNER JOIN BusModel
ON BusVehicle.bus_model_id = BusModel.bus_model_id
INNER JOIN (
    SELECT
        BusLeg.bus_leg_id,
        ARRAY_AGG (
            (
                BusCall.bus_call_id,
                BusCall.call_index,
                (
                    BusStop.bus_stop_id,
                    BusStop.atco_code,
                    BusStop.stop_name,
                    BusStop.locality_name,
                    BusStop.street_name,
                    BusStop.indicator
                )::bus_call_stop_details,
                BusCall.plan_arr,
                BusCall.act_arr,
                BusCall.plan_dep,
                BusCall.act_dep
            )::bus_call_details
            ORDER BY BusCall.call_index
        ) AS leg_calls
    FROM BusLeg
    INNER JOIN BusJourney
    ON BusLeg.bus_journey_id = BusJourney.bus_journey_id
    INNER JOIN BusCall
    ON BusJourney.bus_journey_id = BusCall.bus_journey_id
    INNER JOIN BusStop
    ON BusCall.bus_stop_id = BusStop.bus_stop_id
    WHERE BusCall.call_index >= BusLeg.board_call_index
    AND BusCall.call_index <= BusLeg.alight_call_index
    GROUP BY BusLeg.bus_leg_id
) BusLegCall
ON BusLeg.bus_leg_id = BusLegCall.bus_leg_id;

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
    BusService.bus_service_id,
    (
        BusOperator.bus_operator_id,
        BusOperator.operator_name,
        BusOperator.national_operator_code,
        BusOperator.bg_colour,
        BusOperator.fg_colour
    )::bus_operator_details AS service_operator,
    BusService.service_line,
    BusService.description_outbound,
    OutboundVia.service_vias AS service_outbound_vias,
    BusService.description_inbound,
    InboundVia.service_vias AS service_inbound_vias,
    BusService.bg_colour,
    BusService.fg_colour
FROM BusService
LEFT JOIN (
    SELECT
        bus_service_id,
        ARRAY_AGG(
            BusServiceVia.via_name
            ORDER BY BusServiceVia.via_index
        ) AS service_vias
    FROM BusServiceVia
    WHERE is_outbound = 'true'
    GROUP BY
        BusServiceVia.bus_service_id,
        BusServiceVia.is_outbound
) OutboundVia
ON BusService.bus_service_id = OutboundVia.bus_service_id
LEFT JOIN (
    SELECT
        bus_service_id,
        ARRAY_AGG(
            BusServiceVia.via_name
            ORDER BY BusServiceVia.via_index
        ) AS service_vias
    FROM BusServiceVia
    WHERE is_outbound = 'false'
    GROUP BY
        BusServiceVia.bus_service_id,
        BusServiceVia.is_outbound
) InboundVia
ON BusService.bus_service_id = InboundVia.bus_service_id
INNER JOIN BusOperator
ON BusOperator.bus_operator_id = BusService.bus_operator_id;

CREATE OR REPLACE VIEW bus_vehicle_data AS
SELECT
    BusVehicle.bus_vehicle_id,
    (
        BusOperator.bus_operator_id,
        BusOperator.operator_name,
        BusOperator.national_operator_code,
        BusOperator.bg_colour,
        BusOperator.fg_colour
    )::bus_operator_details AS vehicle_operator,
    BusVehicle.vehicle_identifier,
    BusVehicle.bustimes_id,
    BusVehicle.numberplate,
    BusModel.bus_model_name,
    BusVehicle.livery_style,
    BusVehicle.vehicle_name
FROM BusVehicle
INNER JOIN BusOperator
ON BusVehicle.bus_operator_id = BusOperator.bus_operator_id
INNER JOIN BusModel
ON BusModel.bus_model_id = BusVehicle.bus_model_id;

CREATE OR REPLACE VIEW bus_vehicle_user_details_view AS
SELECT
    BusVehicleLegUserDetails.user_id AS user_id,
    BusVehicle.bus_vehicle_id AS vehicle_id,
    BusVehicle.vehicle_identifier AS vehicle_number,
    BusVehicle.vehicle_name AS vehicle_name,
    BusVehicle.numberplate AS vehicle_numberplate,
    BusOperatorOut.operator_out AS vehicle_operator,
    BusVehicleLegUserDetails.vehicle_legs,
    BusVehicleLegUserDetails.vehicle_duration
FROM BusVehicle
INNER JOIN (
    SELECT (
        bus_operator_id,
        operator_name,
        national_operator_code,
        bg_colour,
        fg_colour)::bus_operator_details AS operator_out
    FROM BusOperator
) BusOperatorOut
ON (BusOperatorOut.operator_out).bus_operator_id = BusVehicle.bus_operator_id
INNER JOIN (
    SELECT
        BusJourney.bus_vehicle_id,
        BusLeg.user_id,
        ARRAY_AGG(
            (
                BusLeg.bus_leg_id,
                (
                    BusService.bus_service_id,
                    BusService.service_line,
                    (
                        BusOperator.bus_operator_id,
                        BusOperator.operator_name,
                        BusOperator.national_operator_code,
                        BusOperator.bg_colour,
                        BusOperator.fg_colour
                    )::bus_operator_details,
                    BusService.description_outbound,
                    BusService.description_inbound,
                    BusService.bg_colour,
                    BusService.fg_colour
                )::bus_leg_service_details,
                BusJourneyCallDetail.bus_journey_call[BusLeg.board_call_index + 1],
                BusJourneyCallDetail.bus_journey_call[BusLeg.alight_call_index + 1],
                COALESCE(
                    (BusJourneyCallDetail.bus_journey_call[BusLeg.alight_call_index + 1]).act_arr,
                    (BusJourneyCallDetail.bus_journey_call[BusLeg.alight_call_index + 1]).act_dep,
                    (BusJourneyCallDetail.bus_journey_call[BusLeg.alight_call_index + 1]).plan_arr,
                    (BusJourneyCallDetail.bus_journey_call[BusLeg.alight_call_index + 1]).plan_dep
                ) -
                COALESCE(
                    (BusJourneyCallDetail.bus_journey_call[BusLeg.board_call_index + 1]).act_dep,
                    (BusJourneyCallDetail.bus_journey_call[BusLeg.board_call_index + 1]).act_arr,
                    (BusJourneyCallDetail.bus_journey_call[BusLeg.board_call_index + 1]).plan_dep,
                    (BusJourneyCallDetail.bus_journey_call[BusLeg.board_call_index + 1]).plan_arr
                )
            )::bus_vehicle_leg_details
        ) AS vehicle_legs,
        SUM(
            COALESCE(
                (BusJourneyCallDetail.bus_journey_call[BusLeg.alight_call_index + 1]).act_arr,
                (BusJourneyCallDetail.bus_journey_call[BusLeg.alight_call_index + 1]).act_dep,
                (BusJourneyCallDetail.bus_journey_call[BusLeg.alight_call_index + 1]).plan_arr,
                (BusJourneyCallDetail.bus_journey_call[BusLeg.alight_call_index + 1]).plan_dep
            ) -
            COALESCE(
                (BusJourneyCallDetail.bus_journey_call[BusLeg.board_call_index + 1]).act_dep,
                (BusJourneyCallDetail.bus_journey_call[BusLeg.board_call_index + 1]).act_arr,
                (BusJourneyCallDetail.bus_journey_call[BusLeg.board_call_index + 1]).plan_dep,
                (BusJourneyCallDetail.bus_journey_call[BusLeg.board_call_index + 1]).plan_arr
            )
        ) AS vehicle_duration
    FROM BusLeg
    INNER JOIN BusJourney
    ON BusLeg.bus_journey_id = BusJourney.bus_journey_id
    INNER JOIN BusService
    ON BusJourney.bus_service_id = BusService.bus_service_id
    INNER JOIN BusOperator
    ON BusService.bus_operator_id = BusOperator.bus_operator_id
    INNER JOIN (
        SELECT
            BusJourney.bus_journey_id,
            ARRAY_AGG((
                BusCall.bus_call_id,
                BusCall.call_index,
                (
                    BusStop.bus_stop_id,
                    BusStop.atco_code,
                    BusStop.stop_name,
                    BusStop.locality_name,
                    BusStop.street_name,
                    BusStop.indicator
                )::bus_call_stop_details,
                BusCall.plan_arr,
                BusCall.act_arr,
                BusCall.plan_dep,
                BusCall.act_dep
            )::bus_call_details ORDER BY call_index) AS bus_journey_call
        FROM BusCall
        INNER JOIN BusJourney
        ON BusCall.bus_journey_id = BusJourney.bus_journey_id
        INNER JOIN BusStop
        ON BusCall.bus_stop_id = BusStop.bus_stop_id
        GROUP BY BusJourney.bus_journey_id
    ) BusJourneyCallDetail
    ON BusJourney.bus_journey_id = BusJourneyCallDetail.bus_journey_id
    GROUP BY (bus_vehicle_id, user_id)
) BusVehicleLegUserDetails
ON BusVehicleLegUserDetails.bus_vehicle_id = BusVehicle.bus_vehicle_id;

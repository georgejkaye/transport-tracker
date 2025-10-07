CREATE OR REPLACE FUNCTION GetBusStops ()
RETURNS SETOF BusStopDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        bus_stop_id,
        atco_code,
        naptan_code,
        stop_name,
        landmark_name,
        street_name,
        crossing_name,
        indicator,
        bearing,
        locality_name,
        parent_locality_name,
        grandparent_locality_name,
        town_name,
        suburb_name,
        latitude,
        longitude
    FROM BusStop
    ORDER BY stop_name ASC, locality_name ASC, indicator ASC;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusStopsByName (
    p_name TEXT
) RETURNS SETOF BusStopDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        bus_stop_id,
        atco_code,
        naptan_code,
        stop_name,
        landmark_name,
        street_name,
        crossing_name,
        indicator,
        bearing,
        locality_name,
        parent_locality_name,
        grandparent_locality_name,
        town_name,
        suburb_name,
        latitude,
        longitude
    FROM BusStop
    WHERE LOWER(stop_name) LIKE '%' || LOWER(p_name) || '%'
    ORDER BY stop_name ASC, locality_name ASC, indicator ASC;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusStopsByAtco (
    p_atcos TEXT[]
) RETURNS SETOF BusStopDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        bus_stop_id,
        atco_code,
        naptan_code,
        stop_name,
        landmark_name,
        street_name,
        crossing_name,
        indicator,
        bearing,
        locality_name,
        parent_locality_name,
        grandparent_locality_name,
        town_name,
        suburb_name,
        latitude,
        longitude
    FROM BusStop
    WHERE atco_code = ANY(p_atcos)
    ORDER BY stop_name ASC, locality_name ASC, indicator ASC;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusStopsByJourney (
    p_journey_id INT
)
RETURNS SETOF BusStopDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusStop.bus_stop_id,
        atco_code,
        naptan_code,
        stop_name,
        landmark_name,
        street_name,
        crossing_name,
        indicator,
        bearing,
        locality_name,
        parent_locality_name,
        grandparent_locality_name,
        town_name,
        suburb_name,
        latitude,
        longitude
    FROM BusStop
    INNER JOIN BusCall
    ON BusStop.bus_stop_id = BusCall.bus_stop_id
    WHERE BusCall.bus_journey_id = p_journey_id
    ORDER BY stop_name ASC, locality_name ASC, indicator ASC;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusOperators ()
RETURNS SETOF BusOperatorDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        bus_operator_id,
        operator_name,
        national_operator_code,
        bg_colour,
        fg_colour
    FROM BusOperator
    ORDER BY operator_name ASC;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusOperatorsByName (
    p_name TEXT
) RETURNS SETOF BusOperatorDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        bus_operator_id,
        operator_name,
        national_operator_code,
        bg_colour,
        fg_colour
    FROM BusOperator
    WHERE LOWER(operator_name) LIKE '%' || LOWER(p_name) || '%'
    ORDER BY operator_name ASC;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusOperatorsByNationalOperatorCode (
    p_noc TEXT
) RETURNS SETOF BusOperatorDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        bus_operator_id,
        operator_name,
        national_operator_code,
        bg_colour,
        fg_colour
    FROM BusOperator
    WHERE LOWER(national_operator_code) = LOWER(p_noc)
    ORDER BY operator_name ASC;
END;
$$;

CREATE OR REPLACE VIEW BusServiceDetailsView AS
SELECT
    BusService.bus_service_id,
    (
        BusOperator.bus_operator_id,
        BusOperator.operator_name,
        BusOperator.national_operator_code,
        BusOperator.bg_colour,
        BusOperator.fg_colour
    )::BusOperatorDetails AS service_operator,
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

CREATE OR REPLACE FUNCTION GetBusServices ()
RETURNS SETOF BusServiceDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusServiceDetailsView.bus_service_id,
        BusServiceDetailsView.service_operator,
        BusServiceDetailsView.service_line,
        BusServiceDetailsView.description_outbound,
        BusServiceDetailsView.service_outbound_vias,
        BusServiceDetailsView.description_inbound,
        BusServiceDetailsView.service_inbound_vias,
        BusServiceDetailsView.bg_colour,
        BusServiceDetailsView.fg_colour
    FROM BusServiceDetailsView;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusServicesByOperatorId (
    p_operator_id INT,
    p_line_name TEXT
) RETURNS SETOF BusServiceDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusServiceDetailsView.bus_service_id,
        BusServiceDetailsView.service_operator,
        BusServiceDetailsView.service_line,
        BusServiceDetailsView.description_outbound,
        BusServiceDetailsView.service_outbound_vias,
        BusServiceDetailsView.description_inbound,
        BusServiceDetailsView.service_inbound_vias,
        BusServiceDetailsView.bg_colour,
        BusServiceDetailsView.fg_colour
    FROM BusServiceDetailsView
    WHERE LOWER(service_line) = LOWER(p_line_name)
    AND (BusServiceDetailsView.service_operator).bus_operator_id = p_operator_id;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusServicesByNationalOperatorCode (
    p_national_operator_code INT,
    p_line_name TEXT
) RETURNS SETOF BusServiceDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusServiceDetailsView.bus_service_id,
        BusServiceDetailsView.service_operator,
        BusServiceDetailsView.service_line,
        BusServiceDetailsView.description_outbound,
        BusServiceDetailsView.service_outbound_vias,
        BusServiceDetailsView.description_inbound,
        BusServiceDetailsView.service_inbound_vias,
        BusServiceDetailsView.bg_colour,
        BusServiceDetailsView.fg_colour
    FROM BusServiceDetailsView
    WHERE LOWER(service_line) = LOWER(p_line_name)
    AND
        (BusServiceDetailsView.service_operator).national_operator_code =
            p_national_operator_code;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusServicesByOperatorName (
    p_name TEXT,
    p_line_name TEXT
) RETURNS SETOF BusServiceDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusServiceDetailsView.bus_service_id,
        BusServiceDetailsView.service_operator,
        BusServiceDetailsView.service_line,
        BusServiceDetailsView.description_outbound,
        BusServiceDetailsView.service_outbound_vias,
        BusServiceDetailsView.description_inbound,
        BusServiceDetailsView.service_inbound_vias,
        BusServiceDetailsView.bg_colour,
        BusServiceDetailsView.fg_colour
    FROM BusServiceDetailsView
    WHERE LOWER(service_line) = LOWER(p_line_name)
    AND
        LOWER((BusServiceDetailsView.service_operator).operator_name)
        LIKE '%' || LOWER(p_name) || '%';
END;
$$;

CREATE OR REPLACE VIEW BusVehicleData AS
SELECT
    BusVehicle.bus_vehicle_id,
    (
        BusOperator.bus_operator_id,
        BusOperator.operator_name,
        BusOperator.national_operator_code,
        BusOperator.bg_colour,
        BusOperator.fg_colour
    )::BusOperatorDetails AS vehicle_operator,
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

CREATE OR REPLACE FUNCTION GetBusVehicles (
    p_operator_id INT,
    p_vehicle_id TEXT
) RETURNS SETOF BusVehicleDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusVehicleData.bus_vehicle_id,
        BusVehicleData.vehicle_operator,
        BusVehicleData.vehicle_identifier,
        BusVehicleData.bustimes_id,
        BusVehicleData.numberplate,
        BusVehicleData.bus_model_name,
        BusVehicleData.livery_style,
        BusVehicleData.vehicle_name
    FROM BusVehicleData
    WHERE
        (p_operator_id IS NULL
        OR (BusVehicleData.vehicle_operator).bus_operator_id = p_operator_id)
    AND
        (p_vehicle_id IS NULL
        OR BusVehicleData.vehicle_identifier= p_vehicle_id);
END;
$$;

CREATE OR REPLACE VIEW BusVehicleUserDetailsView AS
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
        fg_colour)::BusOperatorDetails AS operator_out
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
                    )::BusOperatorDetails,
                    BusService.description_outbound,
                    BusService.description_inbound,
                    BusService.bg_colour,
                    BusService.fg_colour
                )::BusLegServiceDetails,
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
            )::BusVehicleLegDetails
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
                )::BusCallStopDetails,
                BusCall.plan_arr,
                BusCall.act_arr,
                BusCall.plan_dep,
                BusCall.act_dep
            )::BusCallDetails ORDER BY call_index) AS bus_journey_call
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

CREATE OR REPLACE FUNCTION GetUserDetailsForBusVehicles (
    p_user_id INT
) RETURNS SETOF BusVehicleUserDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        vehicle_id,
        vehicle_number,
        vehicle_name,
        vehicle_numberplate,
        vehicle_operator,
        vehicle_legs,
        vehicle_duration
    FROM BusVehicleUserDetailsView
    WHERE user_id = p_user_id
    ORDER BY CARDINALITY(vehicle_legs) DESC;
END;
$$;

CREATE OR REPLACE FUNCTION GetUserDetailsForBusVehicle (
    p_user_id INT,
    p_vehicle_id INT
) RETURNS BusVehicleUserDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN (
        vehicle_id,
        vehicle_number,
        vehicle_name,
        vehicle_numberplate,
        vehicle_operator,
        vehicle_legs,
        vehicle_duration
    )::BusVehicleUserDetails
    FROM BusVehicleUserDetailsView
    WHERE user_id = p_user_id
    AND vehicle_id = p_vehicle_id;
END;
$$;

CREATE OR REPLACE VIEW BusLegUserDetailsView AS
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
        )::BusOperatorDetails,
        BusService.description_outbound,
        BusService.description_inbound,
        BusService.bg_colour,
        BusService.fg_colour
    )::BusLegServiceDetails AS leg_service,
    (
        BusVehicle.bus_vehicle_id,
        (
            BusVehicleOperator.bus_operator_id,
            BusVehicleOperator.operator_name,
            BusVehicleOperator.national_operator_code,
            BusVehicleOperator.bg_colour,
            BusVehicleOperator.fg_colour
        )::BusOperatorDetails,
        BusVehicle.vehicle_identifier,
        BusVehicle.bustimes_id,
        BusVehicle.numberplate,
        BusModel.bus_model_name,
        BusVehicle.livery_style,
        BusVehicle.vehicle_name
    )::BusVehicleDetails AS leg_vehicle,
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
                )::BusCallStopDetails,
                BusCall.plan_arr,
                BusCall.act_arr,
                BusCall.plan_dep,
                BusCall.act_dep
            )::BusCallDetails
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

CREATE OR REPLACE FUNCTION GetUserDetailsForBusLeg(
    p_user_id INT
)
RETURNS SETOF BusLegUserDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusLegUserDetailsView.leg_id,
        BusLegUserDetailsView.leg_service,
        BusLegUserDetailsView.leg_vehicle,
        BusLegUserDetailsView.leg_calls,
        BusLegUserDetailsView.leg_duration
    FROM BusLegUserDetailsView
    WHERE BusLegUserDetailsView.user_id = p_user_id
    ORDER BY COALESCE(
        (BusLegUserDetailsView.leg_calls)[1].act_dep,
        (BusLegUserDetailsView.leg_calls)[1].plan_dep,
        (BusLegUserDetailsView.leg_calls)[1].act_arr,
        (BusLegUserDetailsView.leg_calls)[1].plan_arr);
END;
$$;

CREATE OR REPLACE FUNCTION GetUserDetailsForBusLegsByDatetime(
    p_user_id INT,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF BusLegUserDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusLegUserDetailsView.leg_id,
        BusLegUserDetailsView.leg_service,
        BusLegUserDetailsView.leg_vehicle,
        BusLegUserDetailsView.leg_calls,
        BusLegUserDetailsView.leg_duration
    FROM BusLegUserDetailsView
    WHERE BusLegUserDetailsView.user_id = p_user_id
    AND COALESCE(
        (BusLegUserDetailsView.leg_calls)[1].plan_dep,
        (BusLegUserDetailsView.leg_calls)[1].act_dep,
        (BusLegUserDetailsView.leg_calls)[1].plan_arr,
        (BusLegUserDetailsView.leg_calls)[1].act_arr) >= p_search_start
    AND COALESCE(
        (BusLegUserDetailsView.leg_calls)[1].plan_dep,
        (BusLegUserDetailsView.leg_calls)[1].act_dep,
        (BusLegUserDetailsView.leg_calls)[1].plan_arr,
        (BusLegUserDetailsView.leg_calls)[1].act_arr) <= p_search_end;
END;
$$;

CREATE OR REPLACE FUNCTION GetUserDetailsForBusLegsByStartDatetime(
    p_user_id INT,
    p_search_start TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF BusLegUserDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusLegUserDetailsView.leg_id,
        BusLegUserDetailsView.leg_service,
        BusLegUserDetailsView.leg_vehicle,
        BusLegUserDetailsView.leg_calls,
        BusLegUserDetailsView.leg_duration
    FROM BusLegUserDetailsView
    WHERE BusLegUserDetailsView.user_id = p_user_id
    AND COALESCE(
        (BusLegUserDetailsView.leg_calls)[1].plan_dep,
        (BusLegUserDetailsView.leg_calls)[1].act_dep,
        (BusLegUserDetailsView.leg_calls)[1].plan_arr,
        (BusLegUserDetailsView.leg_calls)[1].act_arr) >= p_search_start;
END;
$$;

CREATE OR REPLACE FUNCTION GetUserDetailsForBusLegsByEndDatetime(
    p_user_id INT,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF BusLegUserDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusLegUserDetailsView.leg_id,
        BusLegUserDetailsView.leg_service,
        BusLegUserDetailsView.leg_vehicle,
        BusLegUserDetailsView.leg_calls,
        BusLegUserDetailsView.leg_duration
    FROM BusLegUserDetailsView
    WHERE BusLegUserDetailsView.user_id = p_user_id
    AND COALESCE(
        (BusLegUserDetailsView.leg_calls)[1].plan_dep,
        (BusLegUserDetailsView.leg_calls)[1].act_dep,
        (BusLegUserDetailsView.leg_calls)[1].plan_arr,
        (BusLegUserDetailsView.leg_calls)[1].act_arr) <= p_search_end;
END;
$$;

CREATE OR REPLACE FUNCTION GetUserDetailsForBusLegsByIds(
    p_user_id INT,
    p_leg_ids INT[]
)
RETURNS SETOF BusLegUserDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusLegUserDetailsView.leg_id,
        BusLegUserDetailsView.leg_service,
        BusLegUserDetailsView.leg_vehicle,
        BusLegUserDetailsView.leg_calls,
        BusLegUserDetailsView.leg_duration
    FROM BusLegUserDetailsView
    WHERE BusLegUserDetailsView.user_id = p_user_id
    AND BusLegUserDetailsView.leg_id = ANY(p_leg_ids);
END;
$$;

CREATE OR REPLACE VIEW BusStopLegDetailsView AS
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
                )::BusOperatorDetails,
                BusService.description_outbound,
                BusService.description_inbound,
                BusService.bg_colour,
                BusService.fg_colour
            )::BusLegServiceDetails,
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
                )::BusCallStopDetails,
                BoardCall.plan_arr,
                BoardCall.act_arr,
                BoardCall.plan_dep,
                BoardCall.act_dep
            )::BusCallDetails,
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
                )::BusCallStopDetails,
                AlightCall.plan_arr,
                AlightCall.act_arr,
                AlightCall.plan_dep,
                AlightCall.act_dep
            )::BusCallDetails,
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
                )::BusCallStopDetails,
                BusCall.plan_arr,
                BusCall.act_arr,
                BusCall.plan_dep,
                BusCall.act_dep
            )::BusCallDetails,
            (BusCall.call_index - BoardCall.call_index),
            (AlightCall.call_index - BusCall.call_index)
        )::BusStopLegDetails
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
INNER JOIN Traveller
ON BusLeg.user_id = Traveller.user_id
WHERE BusCall.call_index >= BoardCall.call_index
AND BusCall.call_index <= AlightCall.call_index
GROUP BY BusStop.bus_stop_id, BusLeg.user_id;

CREATE OR REPLACE FUNCTION GetUserDetailsForBusStop (
    p_user_id INT,
    p_stop_id INT
)
RETURNS BusStopUserDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN
        (
            BusStop.bus_stop_id,
            BusStop.atco_code,
            BusStop.naptan_code,
            BusStop.stop_name,
            BusStop.landmark_name,
            BusStop.street_name,
            BusStop.crossing_name,
            BusStop.indicator,
            BusStop.bearing,
            BusStop.locality_name,
            BusStop.parent_locality_name,
            BusStop.grandparent_locality_name,
            BusStop.town_name,
            BusStop.suburb_name,
            BusStop.latitude,
            BusStop.longitude,
            COALESCE(
                BusStopLegDetailsView.stop_user_legs,
                ARRAY[]::BusStopLegDetails[]
            )
        )::BusStopUserDetails
    FROM BusStop
    LEFT JOIN BusStopLegDetailsView
    ON BusStop.bus_stop_id = BusStopLegDetailsView.bus_stop_id
    AND BusStopLegDetailsView.user_id = p_user_id
    WHERE BusStop.bus_stop_id = p_stop_id;
END;
$$;

CREATE OR REPLACE FUNCTION GetUserDetailsForBusStopByAtco (
    p_user_id INT,
    p_atco TEXT
)
RETURNS BusStopUserDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN
        (
            BusStop.bus_stop_id,
            BusStop.atco_code,
            BusStop.naptan_code,
            BusStop.stop_name,
            BusStop.landmark_name,
            BusStop.street_name,
            BusStop.crossing_name,
            BusStop.indicator,
            BusStop.bearing,
            BusStop.locality_name,
            BusStop.parent_locality_name,
            BusStop.grandparent_locality_name,
            BusStop.town_name,
            BusStop.suburb_name,
            BusStop.latitude,
            BusStop.longitude,
            COALESCE(
                BusStopLegDetailsView.stop_user_legs,
                ARRAY[]::BusStopLegDetails[]
            )
        )::BusStopUserDetails
    FROM BusStop
    LEFT JOIN BusStopLegDetailsView
    ON BusStop.bus_stop_id = BusStopLegDetailsView.bus_stop_id
    AND BusStopLegDetailsView.user_id = p_user_id
    WHERE BusStop.atco_code = p_atco;
END;
$$;

CREATE OR REPLACE FUNCTION GetUserDetailsForBusStops (
    p_user_id INT
)
RETURNS SETOF BusStopUserDetails
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusStop.bus_stop_id,
        BusStop.atco_code,
        BusStop.naptan_code,
        BusStop.stop_name,
        BusStop.landmark_name,
        BusStop.street_name,
        BusStop.crossing_name,
        BusStop.indicator,
        BusStop.bearing,
        BusStop.locality_name,
        BusStop.parent_locality_name,
        BusStop.grandparent_locality_name,
        BusStop.town_name,
        BusStop.suburb_name,
        BusStop.latitude,
        BusStop.longitude,
        COALESCE(
            BusStopLegDetailsView.stop_user_legs,
            ARRAY[]::BusStopLegDetails[]
        )
    FROM BusStop
    INNER JOIN BusStopLegDetailsView
    ON BusStop.bus_stop_id = BusStopLegDetailsView.bus_stop_id
    AND BusStopLegDetailsView.user_id = p_user_id
    ORDER BY BusStop.stop_name, BusStop.locality_name, BusStop.indicator;
END;
$$;
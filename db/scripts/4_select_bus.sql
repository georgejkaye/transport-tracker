CREATE OR REPLACE FUNCTION GetBusStops ()
RETURNS SETOF BusStopOutData
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
    ORDER BY stop_name ASC, locality_name ASC, atco_code ASC;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusStopsByName (
    p_name TEXT
) RETURNS SETOF BusStopOutData
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
    ORDER BY stop_name ASC, locality_name ASC, atco_code ASC;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusStopsByAtco (
    p_atcos TEXT[]
) RETURNS SETOF BusStopOutData
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
    ORDER BY stop_name ASC, locality_name ASC, atco_code ASC;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusStopsByJourney (
    p_journey_id INT
)
RETURNS SETOF BusStopOutData
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
    ORDER BY stop_name ASC, locality_name ASC, atco_code ASC;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusOperators ()
RETURNS SETOF BusOperatorOutData
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
) RETURNS SETOF BusOperatorOutData
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
) RETURNS SETOF BusOperatorOutData
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

CREATE OR REPLACE VIEW BusServiceViaData AS
SELECT
    bus_service_id,
    is_outbound,
    ARRAY_AGG(
        BusServiceVia.via_name
        ORDER BY BusServiceVia.via_index
    ) AS service_vias
    FROM BusServiceVia
    GROUP BY
        BusServiceVia.bus_service_id,
        BusServiceVia.is_outbound;

CREATE OR REPLACE VIEW BusServiceData AS
SELECT
    BusService.bus_service_id,
    (
        BusOperator.bus_operator_id,
        BusOperator.operator_name,
        BusOperator.national_operator_code,
        BusOperator.bg_colour,
        BusOperator.fg_colour
    )::BusOperatorOutData AS service_operator,
    BusService.service_line,
    BusService.description_outbound,
    OutboundVia.service_vias AS service_outbound_vias,
    BusService.description_inbound,
    InboundVia.service_vias AS service_inbound_vias,
    BusService.bg_colour,
    BusService.fg_colour
FROM BusService
LEFT JOIN (
    SELECT bus_service_id, service_vias
    FROM BusServiceViaData
    WHERE is_outbound = 'true'
) OutboundVia
ON BusService.bus_service_id = OutboundVia.bus_service_id
LEFT JOIN (
    SELECT bus_service_id, service_vias
    FROM BusServiceViaData
    WHERE is_outbound = 'false'
) InboundVia
ON BusService.bus_service_id = InboundVia.bus_service_id
INNER JOIN BusOperator
ON BusOperator.bus_operator_id = BusService.bus_operator_id;

CREATE OR REPLACE FUNCTION GetBusServices ()
RETURNS SETOF BusServiceOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT (
        BusServiceData.bus_service_id,
        BusServiceData.bus_operator,
        BusServiceData.service_line,
        BusServiceData.description_outbound,
        BusServiceData.service_outbound_vias,
        BusServiceData.description_inbound,
        BusServiceData.service_inbound_vias,
        BusServiceData.bg_colour,
        BusServiceData.fg_colour
    )::BusServiceOutData
    FROM BusServiceData;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusServicesByOperatorId (
    p_operator_id INT,
    p_line_name TEXT
) RETURNS SETOF BusServiceOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT (
        BusServiceData.bus_service_id,
        BusServiceData.bus_operator,
        BusServiceData.service_line,
        BusServiceData.description_outbound,
        BusServiceData.service_outbound_vias,
        BusServiceData.description_inbound,
        BusServiceData.service_inbound_vias,
        BusServiceData.bg_colour,
        BusServiceData.fg_colour
    )::BusServiceOutData
    FROM BusServiceData
    WHERE LOWER(service_line) = LOWER(p_line_name)
    AND (BusServiceData.bus_operator).bus_operator_id = p_operator_id;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusServicesByNationalOperatorCode (
    p_national_operator_code INT,
    p_line_name TEXT
) RETURNS SETOF BusServiceOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT (
        BusServiceData.bus_service_id,
        BusServiceData.bus_operator,
        BusServiceData.service_line,
        BusServiceData.description_outbound,
        BusServiceData.service_outbound_vias,
        BusServiceData.description_inbound,
        BusServiceData.service_inbound_vias,
        BusServiceData.bg_colour,
        BusServiceData.fg_colour
    )::BusServiceOutData
    FROM BusServiceData
    WHERE LOWER(service_line) = LOWER(p_line_name)
    AND
        (BusServiceData.bus_operator).national_operator_code =
            p_national_operator_code;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusServicesByOperatorName (
    p_name TEXT,
    p_line_name TEXT
) RETURNS SETOF BusServiceOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT (
        BusServiceData.bus_service_id,
        BusServiceData.bus_operator,
        BusServiceData.service_line,
        BusServiceData.description_outbound,
        BusServiceData.service_outbound_vias,
        BusServiceData.description_inbound,
        BusServiceData.service_inbound_vias,
        BusServiceData.bg_colour,
        BusServiceData.fg_colour
    )::BusServiceOutData
    FROM BusServiceData
    WHERE LOWER(service_line) = LOWER(p_line_name)
    AND
        LOWER((BusServiceData.bus_operator).operator_name)
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
    )::BusOperatorOutData AS vehicle_operator,
    BusVehicle.vehicle_identifier,
    BusVehicle.bustimes_id,
    BusVehicle.numberplate,
    BusModel.bus_model_name,
    BusVehicle.livery_style,
    BusVehicle.vehicle_name
FROM BusVehicle
INNER JOIN BusOperator
ON BusVehicle.operator_id = BusOperator.bus_operator_id
INNER JOIN BusModel
ON BusModel.bus_model_id = BusVehicle.bus_model_id;

CREATE OR REPLACE FUNCTION GetBusVehicles (
    p_operator_id INT,
    p_vehicle_id TEXT
) RETURNS SETOF BusVehicleOutData
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
        OR (BusVehicleData.bus_operator).bus_operator_id = p_operator_id)
    AND
        (p_vehicle_id IS NULL
        OR BusVehicleData.vehicle_identifier= p_vehicle_id);
END;
$$;

CREATE OR REPLACE VIEW BusVehicleUserData AS
SELECT
    BusVehicleLegOut.user_id AS user_id,
    BusVehicle.bus_vehicle_id AS vehicle_id,
    BusVehicle.vehicle_identifierAS vehicle_number,
    BusVehicle.operator_name AS vehicle_name,
    BusVehicle.numberplate AS vehicle_numberplate,
    BusOperatorOut.operator_out AS vehicle_operator,
    BusVehicleLegOut.vehicle_legs,
    BusVehicleLegOut.vehicle_duration
FROM BusVehicle
INNER JOIN (
    SELECT (
        bus_operator_id,
        operator_name,
        national_operator_code,
        bg_colour,
        fg_colour)::BusOperatorOutData AS operator_out
    FROM BusOperator
) BusOperatorOut
ON (BusOperatorOut.operator_out).bus_operator_id = BusVehicle.operator_id
INNER JOIN (
    SELECT
        BusJourney.bus_vehicle_id,
        BusLeg.user_id,
        ARRAY_AGG((
            BusLeg.bus_leg_id,
            (
                BusService.bus_service_id,
                BusService.service_line
                BusService.bg_colour,
                BusService.fg_colour
            )::BusServiceOverviewOutData,
            (
                BusOperator.bus_operator_id,
                BusOperator.operator_name,
                BusOperator.national_operator_code,
                BusOperator.bg_colour,
                BusOperator.fg_colour
            )::BusOperatorOutData,
            BusJourneyCall.bus_journey_call[BusLeg.board_call_index + 1],
            BusJourneyCall.bus_journey_call[BusLeg.alight_call_index + 1],
            COALESCE(
                (BusJourneyCall.bus_journey_call[BusLeg.alight_call_index + 1]).act_arr,
                (BusJourneyCall.bus_journey_call[BusLeg.alight_call_index + 1]).act_dep,
                (BusJourneyCall.bus_journey_call[BusLeg.alight_call_index + 1]).plan_arr,
                (BusJourneyCall.bus_journey_call[BusLeg.alight_call_index + 1]).plan_dep
            ) -
            COALESCE(
                (BusJourneyCall.bus_journey_call[BusLeg.board_call_index + 1]).act_dep,
                (BusJourneyCall.bus_journey_call[BusLeg.board_call_index + 1]).act_arr,
                (BusJourneyCall.bus_journey_call[BusLeg.board_call_index + 1]).plan_dep,
                (BusJourneyCall.bus_journey_call[BusLeg.board_call_index + 1]).plan_arr
            ))::BusLegOverviewOutData) AS vehicle_legs,
            SUM(
                COALESCE(
                    (BusJourneyCall.bus_journey_call[BusLeg.alight_call_index + 1]).act_arr,
                    (BusJourneyCall.bus_journey_call[BusLeg.alight_call_index + 1]).act_dep,
                    (BusJourneyCall.bus_journey_call[BusLeg.alight_call_index + 1]).plan_arr,
                    (BusJourneyCall.bus_journey_call[BusLeg.alight_call_index + 1]).plan_dep
                ) -
                COALESCE(
                    (BusJourneyCall.bus_journey_call[BusLeg.board_call_index + 1]).act_dep,
                    (BusJourneyCall.bus_journey_call[BusLeg.board_call_index + 1]).act_arr,
                    (BusJourneyCall.bus_journey_call[BusLeg.board_call_index + 1]).plan_dep,
                    (BusJourneyCall.bus_journey_call[BusLeg.board_call_index + 1]).plan_arr
            )) AS vehicle_duration
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
                )::BusStopOverviewOutData,
                BusCall.plan_arr,
                BusCall.act_arr,
                BusCall.plan_dep,
                BusCall.act_dep
            )::BusCallOverviewOutData ORDER BY call_index) AS bus_journey_call
        FROM BusCall
        INNER JOIN BusJourney
        ON BusCall.bus_journey_id = BusJourney.bus_journey_id
        INNER JOIN BusStop
        ON BusCall.bus_stop_id = BusStop.bus_stop_id
        GROUP BY BusJourney.bus_journey_id
    ) BusJourneyCall
    ON BusJourney.bus_journey_id = BusJourneyCall.bus_journey_id
    GROUP BY (bus_vehicle_id, user_id)
) BusVehicleLegOut
ON BusVehicleLegOut.bus_vehicle_id = BusVehicle.bus_vehicle_id;

CREATE OR REPLACE FUNCTION GetBusVehicleOverviews (
    p_user_id INT
) RETURNS SETOF BusVehicleOverviewOutData
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
    FROM BusVehicleUserData
    WHERE user_id = p_user_id
    ORDER BY CARDINALITY(vehicle_legs) DESC;
END;
$$;

CREATE OR REPLACE VIEW BusCallData AS
SELECT
    BusCall.bus_call_id,
    BusCall.bus_journey_id,
    BusCall.call_index,
    BusCall.bus_stop_id,
    (
        BusStop.bus_stop_id,
        BusStop.atco_code,
        BusStop.stop_name,
        BusStop.locality_name,
        BusStop.street_name,
        BusStop.indicator
    )::BusStopOverviewOutData AS call_stop,
    BusCall.plan_arr,
    BusCall.act_arr,
    BusCall.plan_dep,
    BusCall.act_dep
FROM BusCall
INNER JOIN BusStop
ON BusCall.bus_stop_id = BusStop.bus_stop_id;

CREATE OR REPLACE VIEW BusJourneyCallData AS
SELECT
    BusJourney.bus_journey_id,
    ARRAY_AGG((
        BusCallData.bus_call_id,
        BusCallData.call_index,
        BusCallData.call_stop,
        BusCallData.plan_arr,
        BusCallData.act_arr,
        BusCallData.plan_dep,
        BusCallData.act_dep
    )::BusJourneyCallOutData ORDER BY BusCallData.call_index) AS journey_calls
FROM BusJourney
INNER JOIN BusCallData
ON BusJourney.bus_journey_id = BusCallData.bus_journey_id
GROUP BY BusJourney.bus_journey_id;

CREATE OR REPLACE VIEW BusJourneyData AS
SELECT
    BusJourney.bus_journey_id AS journey_id,
    (
        BusServiceData.bus_service_id,
        BusServiceData.service_operator,
        BusServiceData.service_line,
        BusServiceData.bg_colour,
        BusServiceData.fg_colour
    )::BusJourneyServiceOutData AS journey_service,
    BusJourneyCallData.journey_calls,
    (
        BusVehicleData.bus_vehicle_id,
        BusVehicleData.vehicle_operator,
        BusVehicleData.vehicle_identifier,
        BusVehicleData.bustimes_id,
        BusVehicleData.numberplate,
        BusVehicleData.bus_model_name,
        BusVehicleData.livery_style,
        BusVehicleData.vehicle_name
    )::BusVehicleOutData AS journey_vehicle
FROM BusJourney
INNER JOIN BusServiceData
ON BusJourney.bus_service_id = BusServiceData.bus_service_id
INNER JOIN BusJourneyCallData
ON BusJourney.bus_journey_id = BusJourneyCallData.bus_journey_id
INNER JOIN BusVehicleData
ON BusJourney.bus_vehicle_id = BusVehicleData.bus_vehicle_id;

CREATE OR REPLACE FUNCTION GetBusJourneys (
    p_journey_id INT
) RETURNS SETOF BusJourneyOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusJourneyData.journey_service,
        BusJourneyData.journey_calls,
        BusJourneyData.journey_vehicle
    FROM BusJourneyData
    WHERE p_journey_id IS NULL OR p_journey_id = BusJourney.bus_journey_id;
END;
$$;

CREATE OR REPLACE VIEW BusLegData AS
SELECT
    BusLeg.bus_leg_id AS leg_id,
    (
        Traveller.user_id,
        Traveller.user_name,
        Traveller.display_name
    )::UserOutPublicData AS leg_user,
    (
        BusJourneyData.journey_id,
        BusJourneyData.journey_service,
        BusJourneyData.journey_calls,
        BusJourneyData.journey_vehicle
    )::BusJourneyOutData AS leg_journey,
    BusJourneyData.journey_calls[
        BusLeg.board_call_index + 1:BusLeg.alight_call_index + 1
    ] AS leg_calls
FROM BusLeg
INNER JOIN BusJourneyData
ON BusLeg.bus_journey_id = BusJourneyData.journey_id
INNER JOIN Traveller
ON BusLeg.user_id = Traveller.user_id;

CREATE OR REPLACE FUNCTION GetBusLegs(
    p_user_id INT
)
RETURNS SETOF BusLegOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusLegData.leg_id,
        BusLegData.leg_user,
        BusLegData.leg_journey,
        BusLegData.leg_calls
    FROM BusLegData
    WHERE (BusLegData.leg_user).user_id = p_user_id
    ORDER BY COALESCE(
        (BusLegData.leg_calls)[1].act_dep,
        (BusLegData.leg_calls)[1].plan_dep,
        (BusLegData.leg_calls)[1].act_arr,
        (BusLegData.leg_calls)[1].plan_arr);
END;
$$;

CREATE OR REPLACE FUNCTION GetBusLegsByDatetime(
    p_user_id INT,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF BusLegOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusLegData.leg_id,
        BusLegData.leg_user,
        BusLegData.leg_journey,
        BusLegData.leg_calls
    FROM BusLegData
    WHERE (BusLegData.leg_user).user_id = p_user_id
    AND COALESCE(
        (BusLegData.leg_calls)[1].plan_dep,
        (BusLegData.leg_calls)[1].act_dep,
        (BusLegData.leg_calls)[1].plan_arr,
        (BusLegData.leg_calls)[1].act_arr) >= p_search_start
    AND COALESCE(
        (BusLegData.leg_calls)[1].plan_dep,
        (BusLegData.leg_calls)[1].act_dep,
        (BusLegData.leg_calls)[1].plan_arr,
        (BusLegData.leg_calls)[1].act_arr) <= p_search_end;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusLegsByStartDatetime(
    p_user_id INT,
    p_search_start TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF BusLegOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusLegData.leg_id,
        BusLegData.leg_user,
        BusLegData.leg_journey,
        BusLegData.leg_calls
    FROM BusLegData
    WHERE (BusLegData.leg_user).user_id = p_user_id
    AND COALESCE(
        (BusLegData.leg_calls)[1].plan_dep,
        (BusLegData.leg_calls)[1].act_dep,
        (BusLegData.leg_calls)[1].plan_arr,
        (BusLegData.leg_calls)[1].act_arr) >= p_search_start;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusLegsByEndDatetime(
    p_user_id INT,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF BusLegOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusLegData.leg_id,
        BusLegData.leg_user,
        BusLegData.leg_journey,
        BusLegData.leg_calls
    FROM BusLegData
    WHERE (BusLegData.leg_user).user_id = p_user_id
    AND COALESCE(
        (BusLegData.leg_calls)[1].plan_dep,
        (BusLegData.leg_calls)[1].act_dep,
        (BusLegData.leg_calls)[1].plan_arr,
        (BusLegData.leg_calls)[1].act_arr) <= p_search_end;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusLegsByIds(
    p_user_id INT,
    p_leg_ids INT[]
)
RETURNS SETOF BusLegOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT * FROM BusLegData
    WHERE (BusLegData.leg_user).user_id = p_user_id
    AND BusLegData.leg_id = ANY(p_leg_ids);
END;
$$;
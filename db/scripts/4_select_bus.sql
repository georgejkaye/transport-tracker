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

CREATE OR REPLACE FUNCTION GetBusServiceVias ()
RETURNS SETOF BusServiceViaOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        bus_service_id,
        is_outbound,
        ARRAY_AGG(
            BusServiceViaData.via_name
            ORDER BY BusServiceViaData.via_index
        ) AS service_vias
    FROM (
        SELECT bus_service_id, via_name, via_index, is_outbound
        FROM BusServiceVia
    ) BusServiceViaData
    GROUP BY
        BusServiceViaData.bus_service_id,
        BusServiceViaData.is_outbound;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusServices ()
RETURNS SETOF BusServiceOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH BusViaData AS (
        SELECT
            bus_service_id,
            is_outbound,
            ARRAY_AGG(
                BusServiceViaData.via_name
                ORDER BY BusServiceViaData.via_index
            ) AS service_vias
        FROM (
            SELECT bus_service_id, via_name, via_index, is_outbound
            FROM BusServiceVia
        ) BusServiceViaData
        GROUP BY
            BusServiceViaData.bus_service_id,
            BusServiceViaData.is_outbound
    )
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
        SELECT
            bus_service_id,
            ARRAY_AGG(
                BusServiceViaData.via_name
                ORDER BY BusServiceViaData.via_index
            ) AS service_vias
        FROM (
            SELECT bus_service_id, via_name, via_index
            FROM BusServiceVia
            WHERE is_outbound = 'true'
        ) BusServiceViaData
        GROUP BY BusServiceViaData.bus_service_id
     ) OutboundVia
    ON OutboundVia.bus_service_id = BusService.bus_service_id
    LEFT JOIN (
        SELECT
            bus_service_id,
            ARRAY_AGG(
                BusServiceViaData.via_name
                ORDER BY BusServiceViaData.via_index
            ) AS service_vias
        FROM (
            SELECT bus_service_id, via_name, via_index
            FROM BusServiceVia
            WHERE is_outbound = 'false'
        ) BusServiceViaData
        GROUP BY BusServiceViaData.bus_service_id
     ) InboundVia
    ON InboundVia.bus_service_id = BusService.bus_service_id
    INNER JOIN BusOperator
    ON BusOperator.bus_operator_id = BusService.bus_operator_id;
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
    SELECT * FROM GetBusServices() AllBusService
    WHERE LOWER(service_line) = LOWER(p_line_name)
    AND (AllBusService.bus_operator).bus_operator_id = p_operator_id;
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
    SELECT * FROM GetBusServices() AllBusService
    WHERE LOWER(service_line) = LOWER(p_line_name)
    AND
        (AllBusService.bus_operator).national_operator_code =
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
    SELECT * FROM GetBusServices() AllBusService
    WHERE LOWER(service_line) = LOWER(p_line_name)
    AND
        LOWER((AllBusService.bus_operator).operator_name)
        LIKE '%' || LOWER(p_name) || '%';
END;
$$;

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
        BusVehicle.bus_vehicle_id,
        BusOperatorDetail.bus_operator,
        BusVehicle.vehicle_number,
        BusVehicle.bustimes_id,
        BusVehicle.numberplate,
        BusModel.bus_model_name,
        BusVehicle.livery_style,
        BusVehicle.operator_name
    FROM BusVehicle
    INNER JOIN (
        SELECT
            (BusOperatorObject.getbusoperators).bus_operator_id,
            BusOperatorObject.getbusoperators AS bus_operator
        FROM (SELECT GetBusOperators()) BusOperatorObject
    ) BusOperatorDetail
    ON BusOperatorDetail.bus_operator_id = BusVehicle.operator_id
    INNER JOIN BusModel
    ON BusModel.bus_model_id = BusVehicle.bus_model_id
    WHERE
        (p_operator_id IS NULL
        OR (BusOperatorDetail.bus_operator).bus_operator_id = p_operator_id)
    AND
        (p_vehicle_id IS NULL
        OR BusVehicle.vehicle_number = p_vehicle_id);
END;
$$;

CREATE OR REPLACE VIEW BusVehicleData AS
SELECT
    BusVehicleLegOut.user_id AS user_id,
    BusVehicle.bus_vehicle_id AS vehicle_id,
    BusVehicle.vehicle_number AS vehicle_number,
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
                (BusStop.bus_stop_id,
                BusStop.atco_code,
                BusStop.stop_name,
                BusStop.locality_name,
                BusStop.street_name)::BusStopOverviewOutData,
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
    FROM BusVehicleData
    WHERE user_id = p_user_id
    ORDER BY CARDINALITY(vehicle_legs) DESC;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusCallsByJourney (
    p_journey_id INT
) RETURNS SETOF BusCallOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH BusStopOut AS (
        SELECT GetBusStopsByJourney(p_journey_id) AS bus_stop_out)
    SELECT
        BusCall.bus_call_id,
        BusCall.call_index,
        BusStopOut.bus_stop_out,
        BusCall.plan_arr,
        BusCall.act_arr,
        BusCall.plan_dep,
        BusCall.act_dep
    FROM BusCall
    INNER JOIN BusStopOut
    ON (BusStopOut.bus_stop_out).bus_stop_id = BusCall.bus_stop_id;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusCalls ()
RETURNS SETOF BusCallOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH BusStopOut AS (SELECT GetBusStops() AS bus_stop_out)
    SELECT
        BusCall.bus_call_id,
        BusCall.bus_journey_id,
        BusCall.call_index,
        BusStopOut.bus_stop_out,
        BusCall.plan_arr,
        BusCall.act_arr,
        BusCall.plan_dep,
        BusCall.act_dep
    FROM BusCall
    INNER JOIN (
        SELECT (
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
            longitude)::BusStopOutData AS bus_stop_out
        FROM BusStop
    ) BusStopOut
    ON (BusStopOut.bus_stop_out).bus_stop_id = BusCall.bus_stop_id;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusJourneys (
    p_journey_id INT
) RETURNS SETOF BusJourneyOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusJourney.bus_journey_id AS journey_id,
        BusServiceOut.bus_service_out AS journey_service,
        BusCallArrayOut.bus_calls AS journey_calls,
        BusVehicleOut.bus_vehicle_out AS journey_vehicle
        FROM BusJourney
        INNER JOIN (
            SELECT GetBusServices() AS bus_service_out
        ) BusServiceOut
        ON BusJourney.bus_service_id
            = (BusServiceOut.bus_service_out).bus_service_id
        INNER JOIN (
            SELECT
                (BusCallOut.bus_call_out).journey_id,
                ARRAY_AGG(
                    BusCallOut.bus_call_out
                    ORDER BY (BusCallOut.bus_call_out).call_index)
                    AS bus_calls
            FROM
                (SELECT GetBusCalls() AS bus_call_out) BusCallOut
            GROUP BY (BusCallOut.bus_call_out).journey_id) BusCallArrayOut
        ON BusJourney.bus_journey_id = BusCallArrayOut.journey_id
        INNER JOIN (SELECT GetBusVehicles(NULL, NULL) AS bus_vehicle_out) BusVehicleOut
        ON BusJourney.bus_vehicle_id = (BusVehicleOut.bus_vehicle_out).bus_vehicle_id
        WHERE p_journey_id IS NULL OR p_journey_id = BusJourney.bus_journey_id;
END;
$$;

CREATE OR REPLACE VIEW BusLegData AS
SELECT
    BusLeg.bus_leg_id AS leg_id,
    UserOut.user_out AS leg_user,
    BusJourneyOut.bus_journey_out AS leg_journey,
    (BusJourneyOut.bus_journey_out).journey_calls[
        BusLeg.board_call_index + 1:BusLeg.alight_call_index + 1]
        AS leg_calls
FROM BusLeg
INNER JOIN (SELECT GetBusJourneys(NULL) AS bus_journey_out) BusJourneyOut
ON BusLeg.bus_journey_id = (BusJourneyOut.bus_journey_out).journey_id
INNER JOIN (
    SELECT (user_id, user_name, display_name)::UserOutPublicData AS user_out
    FROM Traveller
) UserOut
ON BusLeg.user_id = (UserOut.user_out).user_id;

CREATE OR REPLACE FUNCTION GetBusLegs(
    p_user_id INT
)
RETURNS SETOF BusLegOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT * FROM BusLegData
    WHERE (BusLegData.leg_user).user_id = p_user_id;
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
    SELECT * FROM BusLegData
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
    SELECT * FROM BusLegData
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
    SELECT * FROM BusLegData
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
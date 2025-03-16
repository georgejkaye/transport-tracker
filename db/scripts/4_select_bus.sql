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
        bus_operator_name,
        bus_operator_national_code,
        bg_colour,
        fg_colour
    FROM BusOperator
    ORDER BY bus_operator_name ASC;
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
        bus_operator_name,
        bus_operator_national_code,
        bg_colour,
        fg_colour
    FROM BusOperator
    WHERE LOWER(bus_operator_name) LIKE '%' || LOWER(p_name) || '%'
    ORDER BY bus_operator_name ASC;
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
        bus_operator_name,
        bus_operator_national_code,
        bg_colour,
        fg_colour
    FROM BusOperator
    WHERE LOWER(bus_operator_national_code) = LOWER(p_noc)
    ORDER BY bus_operator_name ASC;
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
            BusOperator.bus_operator_name,
            BusOperator.bus_operator_national_code,
            BusOperator.bg_colour,
            BusOperator.fg_colour
        )::BusOperatorOutData AS service_operator,
        BusService.service_line,
        BusService.service_description_outbound,
        OutboundVia.service_vias AS service_outbound_vias,
        BusService.service_description_inbound,
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
        (AllBusService.bus_operator).bus_operator_national_code =
            p_national_operator_code;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusServicesByOperatorName (
    p_operator_name TEXT,
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
        LOWER((AllBusService.bus_operator).bus_operator_name)
        LIKE '%' || LOWER(p_operator_name) || '%';
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
        BusVehicle.operator_vehicle_id,
        BusVehicle.bustimes_vehicle_id,
        BusVehicle.bus_numberplate,
        BusModel.bus_model_name,
        BusVehicle.bus_livery_style,
        BusVehicle.bus_name
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
        p_operator_id IS NULL
        OR (BusOperatorDetail.bus_operator).bus_operator_id = p_operator_id
    AND
        p_vehicle_id IS NULL
        OR BusVehicle.operator_vehicle_id = p_vehicle_id;
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
        BusCallArrayOut.bus_calls AS journey_calls
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
        WHERE p_journey_id IS NULL OR p_journey_id = BusJourney.bus_journey_id;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusLegs(
    p_leg_id INT
) RETURNS SETOF BusLegOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        BusLeg.bus_leg_id,
        BusJourneyOut.bus_journey_out,
        BusVehicleOut.bus_vehicle_out,
        (BusJourneyOut.bus_journey_out).journey_calls[
            BusLeg.board_call_index:BusLeg.alight_call_index]
    FROM BusLeg
    INNER JOIN (SELECT GetBusJourneys(NULL) AS bus_journey_out) BusJourneyOut
    ON BusLeg.bus_journey_id = (BusJourneyOut.bus_journey_out).journey_id
    INNER JOIN (SELECT GetBusVehicles(NULL, NULL) AS bus_vehicle_out) BusVehicleOut
    ON BusLeg.bus_vehicle_id = (BusVehicleOut.bus_vehicle_out).bus_vehicle_id
    WHERE p_leg_id IS NULL OR p_leg_id = BusLeg.bus_leg_id;
END;
$$;
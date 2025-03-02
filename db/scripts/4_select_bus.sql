CREATE OR REPLACE FUNCTION GetBusStops (
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
    ORDER BY stop_name ASC;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusStopsFromAtcos (
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
    ORDER BY stop_name ASC;
END;
$$;

CREATE OR REPLACE FUNCTION GetBusOperators (
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
        bus_operator_code,
        bus_operator_national_code,
        bg_colour,
        fg_colour
    FROM BusOperator
    WHERE LOWER(bus_operator_name) LIKE '%' || LOWER(p_name) || '%'
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

CREATE OR REPLACE FUNCTION GetBusServices()
RETURNS SETOF BusServiceOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    WITH BusViaData AS (SELECT * FROM GetBusServiceVias())
    SELECT
        BusService.bus_service_id,
        (
            BusOperator.bus_operator_id,
            BusOperator.bus_operator_name,
            BusOperator.bus_operator_code,
            BusOperator.bus_operator_national_code,
            BusOperator.bg_colour,
            BusOperator.fg_colour
        )::BusOperatorOutData AS service_operator,
        BusService.service_line,
        BusService.service_description_outbound,
        OutboundVia.bus_service_vias AS service_outbound_vias,
        BusService.service_description_inbound,
        InboundVia.bus_service_vias AS service_inbound_vias,
        BusService.bg_colour,
        BusService.fg_colour
    FROM BusService
    LEFT JOIN BusViaData OutboundVia
    ON OutboundVia.bus_service_id = BusService.bus_service_id
    LEFT JOIN BusViaData InboundVia
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

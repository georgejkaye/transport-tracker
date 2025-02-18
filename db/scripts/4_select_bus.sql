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

CREATE OR REPLACE FUNCTION GetBusServices (
    p_line_name TEXT,
    p_operator_id INT
) RETURNS SETOF BusServiceOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT
        bus_service_id,
        bus_operator_id,
        service_line,
        service_description_outbound,
        service_description_inbound,
        bg_colour,
        fg_colour
    FROM BusService
    WHERE LOWER(service_line) LIKE '%' || LOWER(p_line_name) || '%'
    AND bus_operator_id = p_operator_id;
END;
$$;
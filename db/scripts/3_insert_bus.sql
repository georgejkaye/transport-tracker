CREATE OR REPLACE FUNCTION InsertBusStops (
    p_stops BusStopData[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusStop (
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
    ) SELECT
        v_stop.atco_code,
        v_stop.naptan_code,
        v_stop.stop_name,
        v_stop.landmark_name,
        v_stop.street_name,
        v_stop.crossing_name,
        v_stop.indicator,
        v_stop.bearing,
        v_stop.locality_name,
        v_stop.parent_locality_name,
        v_stop.grandparent_locality_name,
        v_stop.town_name,
        v_stop.suburb_name,
        v_stop.latitude,
        v_stop.longitude
    FROM UNNEST(p_stops) AS v_stop;
END;
$$;

CREATE OR REPLACE FUNCTION InsertBusOperators (
    p_operators BusOperatorInData[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusOperator (
        bus_operator_name,
        bus_operator_code,
        bus_operator_national_code
    ) SELECT
        v_operator.bus_operator_name,
        v_operator.bus_operator_code,
        v_operator.bus_operator_national_code
    FROM UNNEST(p_operators) AS v_operator
    ON CONFLICT DO NOTHING;
END;
$$;


CREATE OR REPLACE FUNCTION InsertBusServices (
    p_services BusServiceInData[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusService (
        bus_operator_id,
        bods_line_id,
        service_line,
        service_description_outbound,
        service_description_inbound
    ) SELECT
        (
            SELECT bus_operator_id
            FROM BusOperator
            WHERE bus_operator_national_code
                = v_service.service_operator_national_code
        ),
        v_service.bods_line_id,
        v_service.service_line,
        v_service.service_outbound_description,
        v_service.service_inbound_description
    FROM UNNEST(p_services) AS v_service
    ON CONFLICT DO NOTHING;
END;
$$;

CREATE OR REPLACE FUNCTION InsertBusServiceVias (
    p_vias BusServiceViaInData[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusServiceVia (
        bus_service_id,
        is_outbound,
        via_name,
        via_index
    ) SELECT
        (SELECT bus_service_id
        FROM BusService
        INNER JOIN BusOperator
        On BusService.bus_operator_id = BusOperator.bus_operator_id
        WHERE v_via.service_description =
            CASE WHEN v_via.is_outbound
            THEN service_description_outbound
            ELSE service_description_inbound
            END
        AND
            v_via.service_operator_national_code
                = BusOperator.bus_operator_national_code
        AND v_via.service_line = BusService.service_line
        ),
        v_via.is_outbound,
        v_via.via_name,
        v_via.via_index
    FROM UNNEST(p_vias) AS v_via
    ON CONFLICT DO NOTHING;
END;
$$;

CREATE OR REPLACE FUNCTION InsertTransXChangeBusData (
    p_operators BusOperatorInData[],
    p_services BusServiceInData[],
    p_vias BusServiceViaInData[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    PERFORM InsertBusOperators(p_operators);
    PERFORM InsertBusServices(p_services);
    PERFORM InsertBusServiceVias(p_vias);
END;
$$;
CREATE OR REPLACE FUNCTION insert_bus_services (
    p_services bus_service_in_data_notnull[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusService (
        bus_operator_id,
        bods_line_id,
        service_line,
        description_outbound,
        description_inbound
    ) SELECT
        (
            SELECT bus_operator_id
            FROM BusOperator
            WHERE national_operator_code
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

CREATE OR REPLACE FUNCTION insert_bus_service_vias (
    p_vias bus_service_via_in_data_notnull[]
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
        WHERE bods_line_id = v_via.bods_line_id),
        v_via.is_outbound,
        v_via.via_name,
        v_via.via_index
    FROM UNNEST(p_vias) AS v_via
    ON CONFLICT DO NOTHING;
END;
$$;

CREATE OR REPLACE FUNCTION insert_transxchange_bus_data (
    p_services bus_service_in_data_notnull[],
    p_vias bus_service_via_in_data_notnull[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    PERFORM insert_bus_services(p_services);
    PERFORM insert_bus_service_vias(p_vias);
END;
$$;
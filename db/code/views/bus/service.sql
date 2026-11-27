CREATE OR REPLACE VIEW bus_service_details_view AS
SELECT
    bus_service.bus_service_id,
    (
        bus_operator.bus_operator_id,
        bus_operator.operator_name,
        bus_operator.national_operator_code
    )::bus_operator_summary AS service_operator,
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

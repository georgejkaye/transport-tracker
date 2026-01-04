CREATE OR REPLACE FUNCTION select_bus_service_details ()
RETURNS SETOF bus_service_details
LANGUAGE sql
AS
$$
SELECT
    bus_service_details_view.bus_service_id,
    bus_service_details_view.service_operator,
    bus_service_details_view.service_line,
    bus_service_details_view.description_outbound,
    bus_service_details_view.service_outbound_vias,
    bus_service_details_view.description_inbound,
    bus_service_details_view.service_inbound_vias,
    bus_service_details_view.bg_colour,
    bus_service_details_view.fg_colour
FROM bus_service_details_view;
$$;

CREATE OR REPLACE FUNCTION select_bus_service_details_by_operator_id_and_line_name (
    p_operator_id INTEGER_NOTNULL,
    p_line_name TEXT_NOTNULL
) RETURNS SETOF bus_service_details
LANGUAGE sql
AS
$$
SELECT
    bus_service_details_view.bus_service_id,
    bus_service_details_view.service_operator,
    bus_service_details_view.service_line,
    bus_service_details_view.description_outbound,
    bus_service_details_view.service_outbound_vias,
    bus_service_details_view.description_inbound,
    bus_service_details_view.service_inbound_vias,
    bus_service_details_view.bg_colour,
    bus_service_details_view.fg_colour
FROM bus_service_details_view
WHERE LOWER(service_line) = LOWER(p_line_name)
AND (bus_service_details_view.service_operator).bus_operator_id = p_operator_id;
$$;

CREATE OR REPLACE FUNCTION select_bus_service_details_by_national_operator_code_and_line_name (
    p_national_operator_code TEXT_NOTNULL,
    p_line_name TEXT_NOTNULL
) RETURNS SETOF bus_service_details
LANGUAGE sql
AS
$$
SELECT
    bus_service_details_view.bus_service_id,
    bus_service_details_view.service_operator,
    bus_service_details_view.service_line,
    bus_service_details_view.description_outbound,
    bus_service_details_view.service_outbound_vias,
    bus_service_details_view.description_inbound,
    bus_service_details_view.service_inbound_vias,
    bus_service_details_view.bg_colour,
    bus_service_details_view.fg_colour
FROM bus_service_details_view
WHERE LOWER(service_line) = LOWER(p_line_name)
AND
    (bus_service_details_view.service_operator).national_operator_code =
        p_national_operator_code;
$$;

CREATE OR REPLACE FUNCTION select_bus_service_details_by_operator_name_and_line_name (
    p_operator_name TEXT_NOTNULL,
    p_line_name TEXT_NOTNULL
) RETURNS SETOF bus_service_details
LANGUAGE sql
AS
$$
SELECT
    bus_service_details_view.bus_service_id,
    bus_service_details_view.service_operator,
    bus_service_details_view.service_line,
    bus_service_details_view.description_outbound,
    bus_service_details_view.service_outbound_vias,
    bus_service_details_view.description_inbound,
    bus_service_details_view.service_inbound_vias,
    bus_service_details_view.bg_colour,
    bus_service_details_view.fg_colour
FROM bus_service_details_view
WHERE LOWER(service_line) = LOWER(p_line_name)
AND
    LOWER((bus_service_details_view.service_operator).operator_name)
    LIKE '%' || LOWER(p_operator_name) || '%';
$$;
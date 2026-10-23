DROP TYPE IF EXISTS bus_service_in_data CASCADE;
DROP TYPE IF EXISTS bus_service_via_in_data CASCADE;
DROP TYPE IF EXISTS bus_service_details CASCADE;

DROP DOMAIN IF EXISTS bus_service_in_data_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_service_via_in_data_notnull CASCADE;
DROP DOMAIN IF EXISTS bus_service_details_notnull CASCADE;

CREATE TYPE bus_service_in_data AS (
    service_line TEXT_NOTNULL,
    bods_line_id TEXT_NOTNULL,
    service_operator_national_code TEXT_NOTNULL,
    service_outbound_description TEXT_NOTNULL,
    service_inbound_description TEXT_NOTNULL
);

CREATE DOMAIN bus_service_in_data_notnull
AS bus_service_in_data NOT NULL;

CREATE TYPE bus_service_via_in_data AS (
    bods_line_id TEXT_NOTNULL,
    is_outbound BOOLEAN_NOTNULL,
    via_name TEXT_NOTNULL,
    via_index INTEGER_NOTNULL
);

CREATE DOMAIN bus_service_via_in_data_notnull
AS bus_service_via_in_data NOT NULL;

CREATE TYPE bus_service_details AS (
    bus_service_id INTEGER_NOTNULL,
    bus_operator bus_operator_details_notnull,
    service_line TEXT_NOTNULL,
    description_outbound TEXT,
    service_outbound_vias TEXT_NOTNULL[],
    description_inbound TEXT,
    service_inbound_vias TEXT_NOTNULL[],
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE DOMAIN bus_service_details_notnull
AS bus_service_details NOT NULL;
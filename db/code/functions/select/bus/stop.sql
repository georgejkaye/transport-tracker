CREATE OR REPLACE FUNCTION select_bus_stop_details ()
RETURNS SETOF bus_stop_details
LANGUAGE sql
AS
$$
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
FROM bus_stop
ORDER BY stop_name ASC, locality_name ASC, indicator ASC;
$$;

CREATE OR REPLACE FUNCTION select_bus_stop_details_by_name (
    p_name TEXT_NOTNULL
) RETURNS SETOF bus_stop_details
LANGUAGE sql
AS
$$
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
FROM bus_stop
WHERE LOWER(stop_name) LIKE '%' || LOWER(p_name) || '%'
ORDER BY stop_name ASC, locality_name ASC, indicator ASC;
$$;

CREATE OR REPLACE FUNCTION select_bus_stop_details_by_atcos (
    p_atcos TEXT_NOTNULL[]
) RETURNS SETOF bus_stop_details
LANGUAGE sql
AS
$$
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
FROM bus_stop
WHERE atco_code = ANY(p_atcos)
ORDER BY stop_name ASC, locality_name ASC, indicator ASC;
$$;

CREATE OR REPLACE FUNCTION select_bus_stop_details_by_journey_id (
    p_journey_id INTEGER_NOTNULL
)
RETURNS SETOF bus_stop_details
LANGUAGE sql
AS
$$
SELECT
    bus_stop.bus_stop_id,
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
FROM bus_stop
INNER JOIN bus_call
ON bus_stop.bus_stop_id = bus_call.bus_stop_id
WHERE bus_call.bus_journey_id = p_journey_id
ORDER BY stop_name ASC, locality_name ASC, indicator ASC;
$$;

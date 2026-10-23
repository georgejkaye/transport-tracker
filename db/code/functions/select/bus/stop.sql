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
FROM BusStop
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
FROM BusStop
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
FROM BusStop
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
ORDER BY stop_name ASC, locality_name ASC, indicator ASC;
$$;

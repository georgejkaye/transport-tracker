CREATE OR REPLACE FUNCTION select_bus_stop_user_details_by_user_id_and_stop_id (
    p_user_id INTEGER_NOTNULL,
    p_stop_id INTEGER_NOTNULL
)
RETURNS SETOF bus_stop_user_details
LANGUAGE sql
AS
$$
SELECT
    BusStop.bus_stop_id,
    BusStop.atco_code,
    BusStop.naptan_code,
    BusStop.stop_name,
    BusStop.landmark_name,
    BusStop.street_name,
    BusStop.crossing_name,
    BusStop.indicator,
    BusStop.bearing,
    BusStop.locality_name,
    BusStop.parent_locality_name,
    BusStop.grandparent_locality_name,
    BusStop.town_name,
    BusStop.suburb_name,
    BusStop.latitude,
    BusStop.longitude,
    COALESCE(
        bus_stop_leg_details_view.stop_user_legs,
        ARRAY[]::bus_stop_leg_details[]
    )
FROM BusStop
LEFT JOIN bus_stop_leg_details_view
ON BusStop.bus_stop_id = bus_stop_leg_details_view.bus_stop_id
AND bus_stop_leg_details_view.user_id = p_user_id
WHERE BusStop.bus_stop_id = p_stop_id;
$$;

CREATE OR REPLACE FUNCTION select_bus_stop_user_details_by_user_id_and_atco (
    p_user_id INTEGER_NOTNULL,
    p_atco TEXT_NOTNULL
)
RETURNS SETOF bus_stop_user_details
LANGUAGE sql
AS
$$
SELECT
    BusStop.bus_stop_id,
    BusStop.atco_code,
    BusStop.naptan_code,
    BusStop.stop_name,
    BusStop.landmark_name,
    BusStop.street_name,
    BusStop.crossing_name,
    BusStop.indicator,
    BusStop.bearing,
    BusStop.locality_name,
    BusStop.parent_locality_name,
    BusStop.grandparent_locality_name,
    BusStop.town_name,
    BusStop.suburb_name,
    BusStop.latitude,
    BusStop.longitude,
    COALESCE(
        bus_stop_leg_details_view.stop_user_legs,
        ARRAY[]::bus_stop_leg_details[]
    )
FROM BusStop
LEFT JOIN bus_stop_leg_details_view
ON BusStop.bus_stop_id = bus_stop_leg_details_view.bus_stop_id
AND bus_stop_leg_details_view.user_id = p_user_id
WHERE BusStop.atco_code = p_atco;
$$;

CREATE OR REPLACE FUNCTION select_bus_stop_user_details_by_user_id (
    p_user_id INTEGER_NOTNULL
)
RETURNS SETOF bus_stop_user_details
LANGUAGE sql
AS
$$
SELECT
    BusStop.bus_stop_id,
    BusStop.atco_code,
    BusStop.naptan_code,
    BusStop.stop_name,
    BusStop.landmark_name,
    BusStop.street_name,
    BusStop.crossing_name,
    BusStop.indicator,
    BusStop.bearing,
    BusStop.locality_name,
    BusStop.parent_locality_name,
    BusStop.grandparent_locality_name,
    BusStop.town_name,
    BusStop.suburb_name,
    BusStop.latitude,
    BusStop.longitude,
    COALESCE(
        bus_stop_leg_details_view.stop_user_legs,
        ARRAY[]::bus_stop_leg_details[]
    )
FROM BusStop
INNER JOIN bus_stop_leg_details_view
ON BusStop.bus_stop_id = bus_stop_leg_details_view.bus_stop_id
AND bus_stop_leg_details_view.user_id = p_user_id
ORDER BY BusStop.stop_name, BusStop.locality_name, BusStop.indicator;
$$;
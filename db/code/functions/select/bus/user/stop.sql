CREATE OR REPLACE FUNCTION select_bus_stop_user_details_by_user_id_and_stop_id (
    p_user_id INTEGER_NOTNULL,
    p_stop_id INTEGER_NOTNULL
)
RETURNS SETOF bus_stop_user_details
LANGUAGE sql
AS
$$
SELECT
    bus_stop.bus_stop_id,
    bus_stop.atco_code,
    bus_stop.naptan_code,
    bus_stop.stop_name,
    bus_stop.landmark_name,
    bus_stop.street_name,
    bus_stop.crossing_name,
    bus_stop.indicator,
    bus_stop.bearing,
    bus_stop.locality_name,
    bus_stop.parent_locality_name,
    bus_stop.grandparent_locality_name,
    bus_stop.town_name,
    bus_stop.suburb_name,
    bus_stop.latitude,
    bus_stop.longitude,
    COALESCE(
        bus_stop_leg_details_view.stop_user_legs,
        ARRAY[]::bus_stop_leg_details[]
    )
FROM bus_stop
LEFT JOIN bus_stop_leg_details_view
ON bus_stop.bus_stop_id = bus_stop_leg_details_view.bus_stop_id
AND bus_stop_leg_details_view.user_id = p_user_id
WHERE bus_stop.bus_stop_id = p_stop_id;
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
    bus_stop.bus_stop_id,
    bus_stop.atco_code,
    bus_stop.naptan_code,
    bus_stop.stop_name,
    bus_stop.landmark_name,
    bus_stop.street_name,
    bus_stop.crossing_name,
    bus_stop.indicator,
    bus_stop.bearing,
    bus_stop.locality_name,
    bus_stop.parent_locality_name,
    bus_stop.grandparent_locality_name,
    bus_stop.town_name,
    bus_stop.suburb_name,
    bus_stop.latitude,
    bus_stop.longitude,
    COALESCE(
        bus_stop_leg_details_view.stop_user_legs,
        ARRAY[]::bus_stop_leg_details[]
    )
FROM bus_stop
LEFT JOIN bus_stop_leg_details_view
ON bus_stop.bus_stop_id = bus_stop_leg_details_view.bus_stop_id
AND bus_stop_leg_details_view.user_id = p_user_id
WHERE bus_stop.atco_code = p_atco;
$$;

CREATE OR REPLACE FUNCTION select_bus_stop_user_details_by_user_id (
    p_user_id INTEGER_NOTNULL
)
RETURNS SETOF bus_stop_user_details
LANGUAGE sql
AS
$$
SELECT
    bus_stop.bus_stop_id,
    bus_stop.atco_code,
    bus_stop.naptan_code,
    bus_stop.stop_name,
    bus_stop.landmark_name,
    bus_stop.street_name,
    bus_stop.crossing_name,
    bus_stop.indicator,
    bus_stop.bearing,
    bus_stop.locality_name,
    bus_stop.parent_locality_name,
    bus_stop.grandparent_locality_name,
    bus_stop.town_name,
    bus_stop.suburb_name,
    bus_stop.latitude,
    bus_stop.longitude,
    COALESCE(
        bus_stop_leg_details_view.stop_user_legs,
        ARRAY[]::bus_stop_leg_details[]
    )
FROM bus_stop
INNER JOIN bus_stop_leg_details_view
ON bus_stop.bus_stop_id = bus_stop_leg_details_view.bus_stop_id
AND bus_stop_leg_details_view.user_id = p_user_id
ORDER BY bus_stop.stop_name, bus_stop.locality_name, bus_stop.indicator;
$$;
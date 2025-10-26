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

CREATE OR REPLACE FUNCTION select_bus_operator_details ()
RETURNS SETOF bus_operator_details
LANGUAGE sql
AS
$$
SELECT
    bus_operator_id,
    operator_name,
    national_operator_code,
    bg_colour,
    fg_colour
FROM BusOperator
ORDER BY operator_name ASC;
$$;

CREATE OR REPLACE FUNCTION select_bus_operator_details_by_name (
    p_name TEXT_NOTNULL
) RETURNS SETOF bus_operator_details
LANGUAGE sql
AS
$$
SELECT
    bus_operator_id,
    operator_name,
    national_operator_code,
    bg_colour,
    fg_colour
FROM BusOperator
WHERE LOWER(operator_name) LIKE '%' || LOWER(p_name) || '%'
ORDER BY operator_name ASC;
$$;

CREATE OR REPLACE FUNCTION select_bus_operator_details_by_national_operator_code (
    p_noc TEXT_NOTNULL
) RETURNS SETOF bus_operator_details
LANGUAGE sql
AS
$$
SELECT
    bus_operator_id,
    operator_name,
    national_operator_code,
    bg_colour,
    fg_colour
FROM BusOperator
WHERE LOWER(national_operator_code) = LOWER(p_noc)
ORDER BY operator_name ASC;
$$;

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

CREATE OR REPLACE FUNCTION select_bus_vehicle_details (
    p_operator_id INTEGER,
    p_vehicle_id TEXT_NOTNULL
) RETURNS SETOF bus_vehicle_details
LANGUAGE sql
AS
$$
SELECT
    bus_vehicle_data.bus_vehicle_id,
    bus_vehicle_data.vehicle_operator,
    bus_vehicle_data.vehicle_identifier,
    bus_vehicle_data.bustimes_id,
    bus_vehicle_data.numberplate,
    bus_vehicle_data.bus_model_name,
    bus_vehicle_data.livery_style,
    bus_vehicle_data.vehicle_name
FROM bus_vehicle_data
WHERE
    (p_operator_id IS NULL
    OR (bus_vehicle_data.vehicle_operator).bus_operator_id = p_operator_id)
AND
    (p_vehicle_id IS NULL
    OR bus_vehicle_data.vehicle_identifier= p_vehicle_id);
$$;

CREATE OR REPLACE FUNCTION select_bus_vehicle_user_details_by_user_id (
    p_user_id INTEGER_NOTNULL
) RETURNS SETOF bus_vehicle_user_details
LANGUAGE sql
AS
$$
SELECT
    vehicle_id,
    vehicle_number,
    vehicle_name,
    vehicle_numberplate,
    vehicle_operator,
    vehicle_legs,
    vehicle_duration
FROM bus_vehicle_user_details_view
WHERE user_id = p_user_id
ORDER BY CARDINALITY(vehicle_legs) DESC;
$$;

CREATE OR REPLACE FUNCTION select_bus_vehicle_user_details_by_user_id_and_vehicle_id (
    p_user_id INTEGER_NOTNULL,
    p_vehicle_id INTEGER_NOTNULL
) RETURNS SETOF bus_vehicle_user_details
LANGUAGE sql
AS
$$
SELECT
    vehicle_id,
    vehicle_number,
    vehicle_name,
    vehicle_numberplate,
    vehicle_operator,
    vehicle_legs,
    vehicle_duration
FROM bus_vehicle_user_details_view
WHERE user_id = p_user_id
AND vehicle_id = p_vehicle_id;
$$;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details (
    p_user_id INTEGER_NOTNULL
)
RETURNS SETOF bus_leg_user_details
LANGUAGE sql
AS
$$
SELECT
    bus_leg_user_details_view.leg_id,
    bus_leg_user_details_view.leg_service,
    bus_leg_user_details_view.leg_vehicle,
    bus_leg_user_details_view.leg_calls,
    bus_leg_user_details_view.leg_duration
FROM bus_leg_user_details_view
WHERE bus_leg_user_details_view.user_id = p_user_id
$$;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details_by_user_id_and_datetime (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP_NOTNULL,
    p_search_end TIMESTAMP_NOTNULL
)
RETURNS SETOF bus_leg_user_details
LANGUAGE sql
AS
$$
SELECT
    bus_leg_user_details_view.leg_id,
    bus_leg_user_details_view.leg_service,
    bus_leg_user_details_view.leg_vehicle,
    bus_leg_user_details_view.leg_calls,
    bus_leg_user_details_view.leg_duration
FROM bus_leg_user_details_view
WHERE bus_leg_user_details_view.user_id = p_user_id
AND COALESCE(
    (bus_leg_user_details_view.leg_calls)[1].plan_dep,
    (bus_leg_user_details_view.leg_calls)[1].act_dep,
    (bus_leg_user_details_view.leg_calls)[1].plan_arr,
    (bus_leg_user_details_view.leg_calls)[1].act_arr) >= p_search_start
AND COALESCE(
    (bus_leg_user_details_view.leg_calls)[1].plan_dep,
    (bus_leg_user_details_view.leg_calls)[1].act_dep,
    (bus_leg_user_details_view.leg_calls)[1].plan_arr,
    (bus_leg_user_details_view.leg_calls)[1].act_arr) <= p_search_end;
$$;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details_by_user_id_and_start_datetime (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP_NOTNULL
)
RETURNS SETOF bus_leg_user_details
LANGUAGE sql
AS
$$
SELECT
    bus_leg_user_details_view.leg_id,
    bus_leg_user_details_view.leg_service,
    bus_leg_user_details_view.leg_vehicle,
    bus_leg_user_details_view.leg_calls,
    bus_leg_user_details_view.leg_duration
FROM bus_leg_user_details_view
WHERE bus_leg_user_details_view.user_id = p_user_id
AND COALESCE(
    (bus_leg_user_details_view.leg_calls)[1].plan_dep,
    (bus_leg_user_details_view.leg_calls)[1].act_dep,
    (bus_leg_user_details_view.leg_calls)[1].plan_arr,
    (bus_leg_user_details_view.leg_calls)[1].act_arr) >= p_search_start;
$$;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details_by_user_id_and_end_datetime (
    p_user_id INTEGER_NOTNULL,
    p_search_end TIMESTAMP_NOTNULL
)
RETURNS SETOF bus_leg_user_details
LANGUAGE sql
AS
$$
SELECT
    bus_leg_user_details_view.leg_id,
    bus_leg_user_details_view.leg_service,
    bus_leg_user_details_view.leg_vehicle,
    bus_leg_user_details_view.leg_calls,
    bus_leg_user_details_view.leg_duration
FROM bus_leg_user_details_view
WHERE bus_leg_user_details_view.user_id = p_user_id
AND COALESCE(
    (bus_leg_user_details_view.leg_calls)[1].plan_dep,
    (bus_leg_user_details_view.leg_calls)[1].act_dep,
    (bus_leg_user_details_view.leg_calls)[1].plan_arr,
    (bus_leg_user_details_view.leg_calls)[1].act_arr) <= p_search_end;
$$;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details_by_user_id_and_leg_id (
    p_user_id INTEGER_NOTNULL,
    p_leg_id INTEGER_NOTNULL
)
RETURNS SETOF bus_leg_user_details
LANGUAGE sql
AS
$$
SELECT
    bus_leg_user_details_view.leg_id,
    bus_leg_user_details_view.leg_service,
    bus_leg_user_details_view.leg_vehicle,
    bus_leg_user_details_view.leg_calls,
    bus_leg_user_details_view.leg_duration
FROM bus_leg_user_details_view
WHERE bus_leg_user_details_view.user_id = p_user_id
AND bus_leg_user_details_view.leg_id = p_leg_id
$$;

CREATE OR REPLACE FUNCTION select_bus_leg_user_details_by_user_id_and_leg_ids (
    p_user_id INTEGER_NOTNULL,
    p_leg_ids INTEGER_NOTNULL[]
)
RETURNS SETOF bus_leg_user_details
LANGUAGE sql
AS
$$
SELECT
    bus_leg_user_details_view.leg_id,
    bus_leg_user_details_view.leg_service,
    bus_leg_user_details_view.leg_vehicle,
    bus_leg_user_details_view.leg_calls,
    bus_leg_user_details_view.leg_duration
FROM bus_leg_user_details_view
WHERE bus_leg_user_details_view.user_id = p_user_id
AND bus_leg_user_details_view.leg_id = ANY(P_leg_ids);
$$;

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
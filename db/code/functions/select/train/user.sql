DROP FUNCTION IF EXISTS select_transport_user_train_legs_by_user_id;
DROP FUNCTION IF EXISTS select_transport_user_train_stations_by_user_id;

CREATE FUNCTION select_transport_user_train_legs_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_train_leg_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_id,
    origin,
    destination,
    start_datetime,
    operator,
    brand,
    distance,
    duration,
    delay
FROM transport_user_train_leg_view
WHERE user_id = p_user_id
AND (p_search_start IS NULL OR start_datetime >= p_search_start)
AND (p_search_end IS NULL OR start_datetime <= p_search_end)
ORDER BY start_datetime ASC;
$$;

CREATE FUNCTION select_transport_user_train_stations_by_user_id (
    p_user_id INTEGER_NOTNULL
)
RETURNS SETOF transport_user_train_station_out_data
LANGUAGE sql
AS
$$
SELECT
    train_station_id,
    station_crs,
    station_name,
    station_operator,
    station_brand,
    boards,
    alights,
    calls,
    station_legs
FROM transport_user_train_station_view
WHERE user_id = p_user_id
ORDER BY station_name ASC;
$$;

CREATE FUNCTION select_transport_user_train_station_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_train_station_id INTEGER_NOTNULL
)
RETURNS SETOF transport_user_train_station_out_data
LANGUAGE sql
AS
$$
SELECT
    train_station_id,
    station_crs,
    station_name,
    station_operator,
    station_brand,
    boards,
    alights,
    calls,
    station_legs
FROM transport_user_train_station_view
WHERE user_id = p_user_id
AND train_station_id = p_train_station_id
ORDER BY station_name ASC;
$$;

CREATE FUNCTION select_transport_user_train_stock_class_by_user_id_and_class (
    p_user_id INTEGER_NOTNULL,
    p_stock_class INTEGER_NOTNULL
)
RETURNS SETOF transport_user_train_class_out_data
LANGUAGE sql
AS
$$
SELECT
    transport_user_train_stock_class_view.stock_class,
    transport_user_train_stock_class_view.name,
    transport_user_train_stock_class_view.stock_count,
    transport_user_train_stock_class_view.distance,
    transport_user_train_stock_class_view.duration,
    transport_user_train_stock_class_view.class_legs
FROM transport_user_train_stock_class_view
WHERE user_id = p_user_id
AND stock_class = p_stock_class;
$$;

CREATE FUNCTION select_transport_user_train_stock_class_by_user_id (
    p_user_id INTEGER_NOTNULL
)
RETURNS SETOF transport_user_train_class_high_out_data
LANGUAGE sql
AS
$$
SELECT
    transport_user_train_stock_class_high_view.stock_class,
    transport_user_train_stock_class_high_view.name,
    transport_user_train_stock_class_high_view.stock_count,
    transport_user_train_stock_class_high_view.distance,
    transport_user_train_stock_class_high_view.duration
FROM transport_user_train_stock_class_high_view
WHERE user_id = p_user_id;
$$;

CREATE FUNCTION select_transport_user_train_stock_unit_by_user_id_and_number (
    p_user_id INTEGER_NOTNULL,
    p_stock_number INTEGER_NOTNULL
)
RETURNS SETOF transport_user_train_unit_out_data
LANGUAGE sql
AS
$$
SELECT
    transport_user_train_stock_unit_view.stock_number,
    transport_user_train_stock_unit_view.stock_class,
    transport_user_train_stock_unit_view.stock_subclass,
    transport_user_train_stock_unit_view.stock_cars,
    transport_user_train_stock_unit_view.unit_count,
    transport_user_train_stock_unit_view.distance,
    transport_user_train_stock_unit_view.duration,
    transport_user_train_stock_unit_view.unit_legs
FROM transport_user_train_stock_unit_view
WHERE user_id = p_user_id
AND stock_number = p_stock_number;
$$;

CREATE FUNCTION select_transport_user_train_stock_unit_by_user_id (
    p_user_id INTEGER_NOTNULL
)
RETURNS SETOF transport_user_train_unit_high_out_data
LANGUAGE sql
AS
$$
SELECT
    transport_user_train_stock_unit_high_view.stock_number,
    transport_user_train_stock_unit_high_view.stock_class,
    transport_user_train_stock_unit_high_view.stock_subclass,
    transport_user_train_stock_unit_high_view.stock_cars,
    transport_user_train_stock_unit_high_view.unit_count,
    transport_user_train_stock_unit_high_view.distance,
    transport_user_train_stock_unit_high_view.duration
FROM transport_user_train_stock_unit_high_view
WHERE user_id = p_user_id;
$$;
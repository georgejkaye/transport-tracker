DROP FUNCTION select_station_by_crs;
DROP FUNCTION select_station_by_name;
DROP FUNCTION select_stations_by_name_substring;

DROP VIEW train_station_points_view;
DROP FUNCTION select_train_station_points_by_name;
DROP FUNCTION select_train_station_points_by_names;

CREATE OR REPLACE FUNCTION select_station_by_crs (
    p_station_crs TEXT
)
RETURNS SETOF train_station_out_data
LANGUAGE sql
AS
$$
SELECT
    train_station_id,
    station_crs,
    station_name,
    train_operator_id,
    train_brand_id
FROM train_station
WHERE LOWER(station_crs) = LOWER(p_station_crs)
$$;

CREATE OR REPLACE FUNCTION select_station_by_name (
    p_station_name TEXT
)
RETURNS SETOF train_station_out_data
LANGUAGE sql
AS
$$
SELECT
    train_station.train_station_id,
    train_station.station_crs,
    train_station.station_name,
    train_station.train_operator_id,
    train_station.train_brand_id
FROM train_station
LEFT JOIN train_station_name
ON train_station.train_station_id = train_station_name.train_station_id
WHERE LOWER(station_name) = LOWER(p_station_name)
OR LOWER(alternate_station_name) = LOWER(p_station_name);
$$;

CREATE OR REPLACE FUNCTION select_stations_by_name_substring (
    p_name_substring TEXT
)
RETURNS SETOF train_station_out_data
LANGUAGE sql
AS
$$
SELECT
    train_station_id,
    station_crs,
    station_name,
    train_operator_id,
    train_brand_id
FROM train_station
WHERE LOWER(station_name) LIKE '%' || LOWER(p_name_substring) || '%'
ORDER BY station_name;
$$;

CREATE VIEW train_station_points_view AS
SELECT
    train_station.train_station_id,
    train_station.station_crs,
    train_station.station_name,
    ARRAY_AGG(
        (
            train_station_point.platform,
            train_station_point.latitude,
            train_station_point.longitude
        )::train_station_point_out_data
        ORDER BY train_station_point.platform
    ) AS platform_points
FROM train_station
INNER JOIN train_station_point
ON train_station.train_station_id = train_station_point.station_id
GROUP BY
    train_station.train_station_id,
    train_station.station_crs,
    train_station.station_name;

CREATE OR REPLACE FUNCTION select_train_station_points_by_name (
    p_station_name TEXT
)
RETURNS SETOF train_station_points_out_data
LANGUAGE sql
AS
$$
SELECT
    train_station_points_view.train_station_id,
    train_station_points_view.station_crs,
    train_station_points_view.station_name,
    p_station_name,
    train_station_points_view.platform_points
FROM train_station_points_view
LEFT JOIN train_station_name
ON train_station_points_view.train_station_id
    = train_station_name.train_station_id
WHERE train_station_points_view.station_name = p_station_name
OR train_station_name.alternate_station_name = p_station_name;
$$;

CREATE OR REPLACE FUNCTION select_train_station_points_by_names (
    p_station_name TEXT[]
)
RETURNS SETOF train_station_points_out_data
LANGUAGE sql
AS
$$
SELECT
    train_station_points_view.train_station_id,
    train_station_points_view.station_crs,
    train_station_points_view.station_name,
    train_station_search_name.search_name,
    train_station_points_view.platform_points
FROM train_station_points_view
LEFT JOIN train_station_name
ON train_station_points_view.train_station_id
    = train_station_name.train_station_id
INNER JOIN (
    SELECT UNNEST(p_station_name) AS search_name
) train_station_search_name
ON train_station_points_view.station_name
    = train_station_search_name.search_name
OR train_station_name.alternate_station_name
    = train_station_search_name.search_name;
$$;
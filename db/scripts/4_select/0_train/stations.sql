DROP FUNCTION select_station_by_crs;
DROP FUNCTION select_station_by_name;
DROP FUNCTION select_stations_by_name_substring;
DROP FUNCTION select_station_points_by_names_and_platforms;

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

CREATE OR REPLACE FUNCTION select_station_points_by_names_and_platforms(
    p_station_names train_station_name_point_in_data[]
)
RETURNS SETOF train_station_point_out_data
LANGUAGE sql
AS
$$
WITH inputs AS (
    SELECT *
    FROM UNNEST(p_station_names)
)
SELECT
    train_station.train_station_id,
    train_station.station_crs,
    train_station.station_name,
    COALESCE(
        train_station_point.platform,
        train_station_point_null.platform
    ) AS platform,
    COALESCE(
        train_station_point.latitude,
        train_station_point_null.latitude
    ) AS latitude,
    COALESCE(
        train_station_point.longitude,
        train_station_point_null.longitude
    ) AS longitude
FROM (
    SELECT
        inputs.station_name,
        inputs.platform,
        COALESCE(
            train_station.train_station_id,
            train_station_name.train_station_id
        ) AS train_station_id
    FROM inputs
    LEFT JOIN train_station
    ON LOWER(inputs.station_name)
        = LOWER(train_station.station_name)
    LEFT JOIN train_station_name
    ON LOWER(inputs.station_name)
        = LOWER(train_station_name.alternate_station_name)
) train_station_id
INNER JOIN train_station
ON train_station_id.train_station_id = train_station.train_station_id
LEFT JOIN train_station_point
ON train_station_id.train_station_id = train_station_point.station_id
AND train_station_id.platform = train_station_point.platform
LEFT JOIN train_station_point train_station_point_null
ON train_station_id.train_station_id = train_station_point_null.station_id
AND train_station_point_null.platform IS NULL;
$$;
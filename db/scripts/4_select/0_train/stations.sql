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
RETURNS train_station_out_data
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

CREATE OR REPLACE FUNCTION select_station_by_name_substring (
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
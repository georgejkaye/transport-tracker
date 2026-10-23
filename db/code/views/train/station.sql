DROP VIEW IF EXISTS train_station_points_view CASCADE;

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
ON train_station.train_station_id = train_station_point.train_station_id
GROUP BY
    train_station.train_station_id,
    train_station.station_crs,
    train_station.station_name;

CREATE VIEW train_station_high_view AS
SELECT
    train_station.train_station_id,
    train_station.station_crs,
    train_station.station_name,
    (
        train_operator.train_operator_id,
        train_operator.operator_code,
        train_operator.operator_name
    )::train_operator_high_out_data AS operator,
    CASE
    WHEN train_brand.train_brand_id IS NULL
    THEN
        NULL
    ELSE
        (
            train_brand.train_brand_id,
            train_brand.brand_code,
            train_brand.brand_name
        )::train_operator_high_out_data
    END AS brand
FROM train_station
INNER JOIN train_operator
ON train_station.train_operator_id = train_operator.train_operator_id
LEFT JOIN train_brand
ON train_station.train_brand_id = train_brand.train_brand_id;
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
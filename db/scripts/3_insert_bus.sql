CREATE OR REPLACE FUNCTION InsertBusStops(
    p_stops BusStopData[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusStop (
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
    ) SELECT
        v_stop.atco_code,
        v_stop.naptan_code,
        v_stop.stop_name,
        v_stop.landmark_name,
        v_stop.street_name,
        v_stop.crossing_name,
        v_stop.indicator,
        v_stop.bearing,
        v_stop.locality_name,
        v_stop.parent_locality_name,
        v_stop.grandparent_locality_name,
        v_stop.town_name,
        v_stop.suburb_name,
        v_stop.latitude,
        v_stop.longitude
    FROM UNNEST(p_stops) AS v_stop;
END;
$$;
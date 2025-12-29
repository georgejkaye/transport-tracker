DROP FUNCTION IF EXISTS select_transport_user_train_stations_by_user_id;
DROP FUNCTION IF EXISTS select_transport_user_train_station_by_user_id_and_station_id;
DROP FUNCTION IF EXISTS select_transport_user_train_station_by_user_id_and_station_crs;

CREATE FUNCTION select_transport_user_train_stations_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_train_station_high_out_data
LANGUAGE sql
AS
$$
SELECT
    train_station_high_view.train_station_id,
    train_station_high_view.station_crs,
    train_station_high_view.station_name,
    train_station_high_view.operator,
    train_station_high_view.brand,
    train_station_leg_stat.boards,
    train_station_leg_stat.alights,
    train_station_leg_stat.total
        - train_station_leg_stat.boards
        - train_station_leg_stat.alights
        AS calls
FROM train_station_high_view
INNER JOIN (
    SELECT
        train_station_leg_view.train_station_id,
        COUNT(*) AS total,
        COUNT(
            CASE
            WHEN
                COALESCE(
                    train_station_leg_view.plan_dep,
                    train_station_leg_view.act_dep
                ) = train_leg_high_view.board_time
            THEN 1
            END
        ) AS boards,
        COUNT(
            CASE
            WHEN
                COALESCE(
                    train_station_leg_view.plan_arr,
                    train_station_leg_view.act_arr
                ) = train_leg_high_view.alight_time
            THEN 1
            END
        ) AS alights
    FROM train_station_leg_view
    INNER JOIN train_leg_high_view
    ON train_station_leg_view.train_leg_id = train_leg_high_view.train_leg_id
    INNER JOIN transport_user_train_leg
    ON train_station_leg_view.train_leg_id
        = transport_user_train_leg.train_leg_id
    WHERE transport_user_train_leg.user_id = p_user_id
    AND (
        p_search_start IS NULL
        OR train_leg_high_view.board_time >= p_search_start
    )
    AND (
        p_search_end IS NULL
        OR train_leg_high_view.alight_time < p_search_end
    )
    GROUP BY
        train_station_leg_view.train_station_id
) train_station_leg_stat
ON train_station_high_view.train_station_id
    = train_station_leg_stat.train_station_id
ORDER BY station_name ASC;
$$;

CREATE FUNCTION select_transport_user_train_station_by_user_id_and_station_id (
    p_user_id INTEGER_NOTNULL,
    p_train_station_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_train_station_out_data
LANGUAGE sql
AS
$$
SELECT
    train_station_high_view.train_station_id,
    train_station_high_view.station_crs,
    train_station_high_view.station_name,
    train_station_high_view.operator,
    train_station_high_view.brand,
    train_station_leg_stat.boards,
    train_station_leg_stat.alights,
    train_station_leg_stat.total
        - train_station_leg_stat.boards
        - train_station_leg_stat.alights
        AS calls,
    train_station_leg_stat.legs
FROM train_station_high_view
INNER JOIN (
    SELECT
        train_station_leg_view.train_station_id,
        COUNT(*) AS total,
        COUNT(
            CASE
            WHEN
                COALESCE(
                    train_station_leg_view.plan_dep,
                    train_station_leg_view.act_dep
                ) = train_leg_high_view.board_time
            THEN 1
            END
        ) AS boards,
        COUNT(
            CASE
            WHEN
                COALESCE(
                    train_station_leg_view.plan_arr,
                    train_station_leg_view.act_arr
                ) = train_leg_high_view.alight_time
            THEN 1
            END
        ) AS alights,
        ARRAY_AGG(
            (
                train_station_leg_view.train_leg_id,
                train_station_leg_view.board_station,
                train_station_leg_view.alight_station,
                train_station_leg_view.plan_arr,
                train_station_leg_view.act_arr,
                train_station_leg_view.plan_dep,
                train_station_leg_view.act_dep,
                train_station_leg_view.operator,
                train_station_leg_view.brand,
                train_station_leg_view.call_index,
                train_station_leg_view.calls_before,
                train_station_leg_view.calls_after
            )::transport_user_train_station_leg_out_data
        ) AS legs
    FROM train_station_leg_view
    INNER JOIN train_leg_high_view
    ON train_station_leg_view.train_leg_id = train_leg_high_view.train_leg_id
    INNER JOIN transport_user_train_leg
    ON train_station_leg_view.train_leg_id
        = transport_user_train_leg.train_leg_id
    WHERE transport_user_train_leg.user_id = p_user_id
    AND (
        p_search_start IS NULL
        OR train_leg_high_view.board_time >= p_search_start
    )
    AND (
        p_search_end IS NULL
        OR train_leg_high_view.alight_time < p_search_end
    )
    GROUP BY
        train_station_leg_view.train_station_id
) train_station_leg_stat
ON train_station_high_view.train_station_id
    = train_station_leg_stat.train_station_id
WHERE train_station_high_view.train_station_id = p_train_station_id;
$$;

CREATE FUNCTION select_transport_user_train_station_by_user_id_and_station_crs (
    p_user_id INTEGER_NOTNULL,
    p_station_crs TEXT_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_train_station_out_data
LANGUAGE sql
AS
$$
SELECT
    train_station_high_view.train_station_id,
    train_station_high_view.station_crs,
    train_station_high_view.station_name,
    train_station_high_view.operator,
    train_station_high_view.brand,
    train_station_leg_stat.boards,
    train_station_leg_stat.alights,
    train_station_leg_stat.total
        - train_station_leg_stat.boards
        - train_station_leg_stat.alights
        AS calls,
    train_station_leg_stat.legs
FROM train_station_high_view
INNER JOIN (
    SELECT
        train_station_leg_view.train_station_id,
        COUNT(*) AS total,
        COUNT(
            CASE
            WHEN
                COALESCE(
                    train_station_leg_view.plan_dep,
                    train_station_leg_view.act_dep
                ) = train_leg_high_view.board_time
            THEN 1
            END
        ) AS boards,
        COUNT(
            CASE
            WHEN
                COALESCE(
                    train_station_leg_view.plan_arr,
                    train_station_leg_view.act_arr
                ) = train_leg_high_view.alight_time
            THEN 1
            END
        ) AS alights,
        ARRAY_AGG(
            (
                train_station_leg_view.train_leg_id,
                train_station_leg_view.board_station,
                train_station_leg_view.alight_station,
                train_station_leg_view.plan_arr,
                train_station_leg_view.act_arr,
                train_station_leg_view.plan_dep,
                train_station_leg_view.act_dep,
                train_station_leg_view.operator,
                train_station_leg_view.brand,
                train_station_leg_view.call_index,
                train_station_leg_view.calls_before,
                train_station_leg_view.calls_after
            )::transport_user_train_station_leg_out_data
        ) AS legs
    FROM train_station_leg_view
    INNER JOIN train_leg_high_view
    ON train_station_leg_view.train_leg_id = train_leg_high_view.train_leg_id
    INNER JOIN transport_user_train_leg
    ON train_station_leg_view.train_leg_id
        = transport_user_train_leg.train_leg_id
    WHERE transport_user_train_leg.user_id = p_user_id
    AND (
        p_search_start IS NULL
        OR train_leg_high_view.board_time >= p_search_start
    )
    AND (
        p_search_end IS NULL
        OR train_leg_high_view.alight_time < p_search_end
    )
    GROUP BY
        train_station_leg_view.train_station_id
) train_station_leg_stat
ON train_station_high_view.train_station_id
    = train_station_leg_stat.train_station_id
WHERE train_station_high_view.station_crs = p_station_crs;
$$;

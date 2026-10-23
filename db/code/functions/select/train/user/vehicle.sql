DROP FUNCTION IF EXISTS select_transport_user_train_class_by_user_id_and_class;
DROP FUNCTION IF EXISTS select_transport_user_train_class_by_user_id;
DROP FUNCTION IF EXISTS select_top_transport_user_train_classes_by_user_id;
DROP FUNCTION IF EXISTS select_transport_user_train_class_stats_by_user_id;
DROP FUNCTION IF EXISTS select_transport_user_train_unit_by_user_id_and_number;
DROP FUNCTION IF EXISTS select_transport_user_train_unit_by_user_id;
DROP FUNCTION IF EXISTS select_top_transport_user_train_units_by_user_id;
DROP FUNCTION IF EXISTS select_transport_user_train_unit_stats_by_user_id;

CREATE FUNCTION select_transport_user_train_class_by_user_id_and_class (
    p_user_id INTEGER_NOTNULL,
    p_stock_class INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_train_class_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_class_stock.stock_class,
    train_stock.name,
    train_leg_class_stock.count,
    train_leg_class_stock.distance,
    train_leg_class_stock.duration,
    train_leg_class_stock.legs
FROM (
    SELECT
        train_leg_stock_class_view.stock_class,
        COUNT(train_leg_stock_class_view.*) AS count,
        SUM(train_leg_stock_class_view.distance) AS distance,
        SUM(train_leg_stock_class_view.duration) AS duration,
        ARRAY_AGG(
            (
                train_leg_high_view.train_leg_id,
                train_leg_high_view.board_time,
                train_leg_high_view.board_station,
                train_leg_high_view.alight_station,
                train_leg_high_view.operator,
                train_leg_high_view.brand,
                train_leg_stock_class_view.units,
                train_leg_stock_class_view.distance,
                train_leg_stock_class_view.duration
            )::transport_user_train_class_leg_out_data
            ORDER BY train_leg_high_view.board_time
        ) AS legs
    FROM train_leg_stock_class_view
    INNER JOIN train_leg_high_view
    ON train_leg_stock_class_view.train_leg_id
        = train_leg_high_view.train_leg_id
    INNER JOIN transport_user_train_leg
    ON train_leg_stock_class_view.train_leg_id
        = transport_user_train_leg.train_leg_id
    WHERE transport_user_train_leg.user_id = p_user_id
    AND (
        p_search_start IS NULL
        OR train_leg_high_view.board_time >= p_search_start
    )
    AND (
        p_search_end IS NULL
        OR train_leg_high_view.board_time < p_search_end
    )
    GROUP BY
        user_id,
        train_leg_stock_class_view.stock_class
) train_leg_class_stock
INNER JOIN train_stock
ON train_leg_class_stock.stock_class = train_stock.stock_class
WHERE train_leg_class_stock.stock_class = p_stock_class;
$$;

CREATE FUNCTION select_transport_user_train_class_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_train_class_high_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_class_stock.stock_class,
    train_stock.name,
    train_leg_class_stock.count,
    train_leg_class_stock.distance,
    train_leg_class_stock.duration
FROM (
    SELECT
        train_leg_stock_class_stats_view.stock_class,
        COUNT(train_leg_stock_class_stats_view.*) AS count,
        SUM(train_leg_stock_class_stats_view.distance) AS distance,
        SUM(train_leg_stock_class_stats_view.duration) AS duration
    FROM train_leg_stock_class_stats_view
    INNER JOIN train_leg_high_view
    ON train_leg_stock_class_stats_view.train_leg_id
        = train_leg_high_view.train_leg_id
    INNER JOIN transport_user_train_leg
    ON train_leg_stock_class_stats_view.train_leg_id
        = transport_user_train_leg.train_leg_id
    WHERE transport_user_train_leg.user_id = p_user_id
    AND (
        p_search_start IS NULL
        OR train_leg_high_view.board_time >= p_search_start
    )
    AND (
        p_search_end IS NULL
        OR train_leg_high_view.board_time < p_search_end
    )
    GROUP BY
        user_id,
        train_leg_stock_class_stats_view.stock_class
) train_leg_class_stock
INNER JOIN train_stock
ON train_leg_class_stock.stock_class = train_stock.stock_class
ORDER BY train_leg_class_stock.stock_class;
$$;

CREATE FUNCTION select_top_transport_user_train_classes_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE,
    p_rows_to_return INTEGER
)
RETURNS SETOF transport_user_train_class_high_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_class_stock.stock_class,
    train_stock.name,
    train_leg_class_stock.count,
    train_leg_class_stock.distance,
    train_leg_class_stock.duration
FROM (
    SELECT
        train_leg_stock_class_stats_view.stock_class,
        COUNT(train_leg_stock_class_stats_view.*) AS count,
        SUM(train_leg_stock_class_stats_view.distance) AS distance,
        SUM(train_leg_stock_class_stats_view.duration) AS duration
    FROM train_leg_stock_class_stats_view
    INNER JOIN train_leg_high_view
    ON train_leg_stock_class_stats_view.train_leg_id
        = train_leg_high_view.train_leg_id
    INNER JOIN transport_user_train_leg
    ON train_leg_stock_class_stats_view.train_leg_id
        = transport_user_train_leg.train_leg_id
    WHERE transport_user_train_leg.user_id = p_user_id
    AND (
        p_search_start IS NULL
        OR train_leg_high_view.board_time >= p_search_start
    )
    AND (
        p_search_end IS NULL
        OR train_leg_high_view.board_time < p_search_end
    )
    GROUP BY
        user_id,
        train_leg_stock_class_stats_view.stock_class
) train_leg_class_stock
INNER JOIN train_stock
ON train_leg_class_stock.stock_class = train_stock.stock_class
ORDER BY
    train_leg_class_stock.count DESC,
    train_leg_class_stock.distance DESC,
    train_leg_class_stock.duration DESC
LIMIT p_rows_to_return;
$$;

CREATE FUNCTION select_transport_user_train_class_stats_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_train_class_stats
LANGUAGE sql
AS
$$
SELECT
    COUNT(*) AS count
FROM (
    SELECT
        train_leg_stock_class_stats_view.stock_class,
        COUNT(train_leg_stock_class_stats_view.*) AS count,
        SUM(train_leg_stock_class_stats_view.distance) AS distance,
        SUM(train_leg_stock_class_stats_view.duration) AS duration
    FROM train_leg_stock_class_stats_view
    INNER JOIN train_leg_high_view
    ON train_leg_stock_class_stats_view.train_leg_id
        = train_leg_high_view.train_leg_id
    INNER JOIN transport_user_train_leg
    ON train_leg_stock_class_stats_view.train_leg_id
        = transport_user_train_leg.train_leg_id
    WHERE transport_user_train_leg.user_id = p_user_id
    AND (
        p_search_start IS NULL
        OR train_leg_high_view.board_time >= p_search_start
    )
    AND (
        p_search_end IS NULL
        OR train_leg_high_view.board_time < p_search_end
    )
    GROUP BY
        user_id,
        train_leg_stock_class_stats_view.stock_class
) train_leg_class_stock
INNER JOIN train_stock
ON train_leg_class_stock.stock_class = train_stock.stock_class;
$$;

CREATE FUNCTION select_transport_user_train_unit_by_user_id_and_number (
    p_user_id INTEGER_NOTNULL,
    p_stock_number INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_train_unit_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_unit_stock.stock_number,
    train_leg_unit_stock.stock_class,
    train_leg_unit_stock.stock_subclass,
    train_leg_unit_stock.stock_cars,
    train_leg_unit_stock.count,
    train_leg_unit_stock.distance,
    train_leg_unit_stock.duration,
    train_leg_unit_stock.legs
FROM (
    SELECT
        train_leg_stock_unit_view.stock_number,
        train_leg_stock_unit_view.stock_class,
        train_leg_stock_unit_view.stock_subclass,
        train_leg_stock_unit_view.stock_cars,
        COUNT(train_leg_stock_unit_view.*) AS count,
        SUM(train_leg_stock_unit_view.distance) AS distance,
        SUM(train_leg_stock_unit_view.duration) AS duration,
        ARRAY_AGG(
            (
                train_leg_high_view.train_leg_id,
                train_leg_high_view.board_time,
                train_leg_high_view.board_station,
                train_leg_high_view.alight_station,
                train_leg_high_view.operator,
                train_leg_high_view.brand,
                train_leg_stock_unit_view.segments,
                train_leg_stock_unit_view.distance,
                train_leg_stock_unit_view.duration
            )::transport_user_train_unit_leg_out_data
            ORDER BY train_leg_high_view.board_time
        ) AS legs
    FROM train_leg_stock_unit_view
    INNER JOIN train_leg_high_view
    ON train_leg_stock_unit_view.train_leg_id
        = train_leg_high_view.train_leg_id
    INNER JOIN transport_user_train_leg
    ON train_leg_stock_unit_view.train_leg_id
        = transport_user_train_leg.train_leg_id
    WHERE transport_user_train_leg.user_id = p_user_id
    AND (
        p_search_start IS NULL
        OR train_leg_high_view.board_time >= p_search_start
    )
    AND (
        p_search_end IS NULL
        OR train_leg_high_view.board_time < p_search_end
    )
    GROUP BY
        user_id,
        train_leg_stock_unit_view.stock_number,
        train_leg_stock_unit_view.stock_class,
        train_leg_stock_unit_view.stock_subclass,
        train_leg_stock_unit_view.stock_cars
) train_leg_unit_stock
WHERE train_leg_unit_stock.stock_number = p_stock_number;
$$;

CREATE FUNCTION select_transport_user_train_unit_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_train_unit_high_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_unit_stock.stock_number,
    train_leg_unit_stock.stock_class,
    train_leg_unit_stock.stock_subclass,
    train_leg_unit_stock.stock_cars,
    train_leg_unit_stock.count,
    train_leg_unit_stock.distance,
    train_leg_unit_stock.duration
FROM (
    SELECT
        train_leg_stock_unit_stats_view.stock_number,
        train_leg_stock_unit_stats_view.stock_class,
        train_leg_stock_unit_stats_view.stock_subclass,
        train_leg_stock_unit_stats_view.stock_cars,
        COUNT(train_leg_stock_unit_stats_view.*) AS count,
        SUM(train_leg_stock_unit_stats_view.distance) AS distance,
        SUM(train_leg_stock_unit_stats_view.duration) AS duration
    FROM train_leg_stock_unit_stats_view
    INNER JOIN train_leg_high_view
    ON train_leg_stock_unit_stats_view.train_leg_id
        = train_leg_high_view.train_leg_id
    INNER JOIN transport_user_train_leg
    ON train_leg_stock_unit_stats_view.train_leg_id
        = transport_user_train_leg.train_leg_id
    WHERE transport_user_train_leg.user_id = p_user_id
    AND (
        p_search_start IS NULL
        OR train_leg_high_view.board_time >= p_search_start
    )
    AND (
        p_search_end IS NULL
        OR train_leg_high_view.board_time < p_search_end
    )
    GROUP BY
        user_id,
        -- TODO explicit stock unit table
        train_leg_stock_unit_stats_view.stock_number,
        train_leg_stock_unit_stats_view.stock_class,
        train_leg_stock_unit_stats_view.stock_subclass,
        train_leg_stock_unit_stats_view.stock_cars
) train_leg_unit_stock
ORDER BY train_leg_unit_stock.stock_number;
$$;

CREATE FUNCTION select_top_transport_user_train_units_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE,
    p_rows_to_return INTEGER_NOTNULL
)
RETURNS SETOF transport_user_train_unit_high_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_unit_stock.stock_number,
    train_leg_unit_stock.stock_class,
    train_leg_unit_stock.stock_subclass,
    train_leg_unit_stock.stock_cars,
    train_leg_unit_stock.count,
    train_leg_unit_stock.distance,
    train_leg_unit_stock.duration
FROM (
    SELECT
        train_leg_stock_unit_stats_view.stock_number,
        train_leg_stock_unit_stats_view.stock_class,
        train_leg_stock_unit_stats_view.stock_subclass,
        train_leg_stock_unit_stats_view.stock_cars,
        COUNT(train_leg_stock_unit_stats_view.*) AS count,
        SUM(train_leg_stock_unit_stats_view.distance) AS distance,
        SUM(train_leg_stock_unit_stats_view.duration) AS duration
    FROM train_leg_stock_unit_stats_view
    INNER JOIN train_leg_high_view
    ON train_leg_stock_unit_stats_view.train_leg_id
        = train_leg_high_view.train_leg_id
    INNER JOIN transport_user_train_leg
    ON train_leg_stock_unit_stats_view.train_leg_id
        = transport_user_train_leg.train_leg_id
    WHERE transport_user_train_leg.user_id = p_user_id
    AND (
        p_search_start IS NULL
        OR train_leg_high_view.board_time >= p_search_start
    )
    AND (
        p_search_end IS NULL
        OR train_leg_high_view.board_time < p_search_end
    )
    GROUP BY
        user_id,
        -- TODO explicit stock unit table
        train_leg_stock_unit_stats_view.stock_number,
        train_leg_stock_unit_stats_view.stock_class,
        train_leg_stock_unit_stats_view.stock_subclass,
        train_leg_stock_unit_stats_view.stock_cars
) train_leg_unit_stock
ORDER BY
    train_leg_unit_stock.count DESC,
    train_leg_unit_stock.distance DESC,
    train_leg_unit_stock.duration DESC
LIMIT p_rows_to_return;
$$;

CREATE FUNCTION select_transport_user_train_unit_stats_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF transport_user_train_unit_stats
LANGUAGE sql
AS
$$
SELECT
    COUNT(*) AS count
FROM (
    SELECT
        train_leg_stock_unit_stats_view.stock_number,
        train_leg_stock_unit_stats_view.stock_class,
        train_leg_stock_unit_stats_view.stock_subclass,
        train_leg_stock_unit_stats_view.stock_cars,
        COUNT(train_leg_stock_unit_stats_view.*) AS count,
        SUM(train_leg_stock_unit_stats_view.distance) AS distance,
        SUM(train_leg_stock_unit_stats_view.duration) AS duration
    FROM train_leg_stock_unit_stats_view
    INNER JOIN train_leg_high_view
    ON train_leg_stock_unit_stats_view.train_leg_id
        = train_leg_high_view.train_leg_id
    INNER JOIN transport_user_train_leg
    ON train_leg_stock_unit_stats_view.train_leg_id
        = transport_user_train_leg.train_leg_id
    WHERE transport_user_train_leg.user_id = p_user_id
    AND (
        p_search_start IS NULL
        OR train_leg_high_view.board_time >= p_search_start
    )
    AND (
        p_search_end IS NULL
        OR train_leg_high_view.board_time < p_search_end
    )
    GROUP BY
        user_id,
        -- TODO explicit stock unit table
        train_leg_stock_unit_stats_view.stock_number,
        train_leg_stock_unit_stats_view.stock_class,
        train_leg_stock_unit_stats_view.stock_subclass,
        train_leg_stock_unit_stats_view.stock_cars
) train_leg_unit_stock
$$;
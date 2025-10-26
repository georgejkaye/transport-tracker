DROP FUNCTION IF EXISTS select_train_leg_by_id;
DROP FUNCTION IF EXISTS select_train_legs_by_ids;

DROP FUNCTION IF EXISTS select_train_leg_points_by_leg_id;
DROP FUNCTION IF EXISTS select_train_leg_points_by_leg_ids;
DROP FUNCTION IF EXISTS select_train_leg_points_by_user_id;

CREATE OR REPLACE FUNCTION select_train_leg_by_id (
    p_train_leg_id INTEGER_NOTNULL
)
RETURNS SETOF train_leg_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_view.train_leg_id,
    train_leg_view.services,
    train_leg_view.calls,
    train_leg_view.stock
FROM train_leg_view
WHERE train_leg_view.train_leg_id = p_train_leg_id;
$$;

CREATE OR REPLACE FUNCTION select_train_legs_by_ids (
    p_train_leg_ids INTEGER_NOTNULL[]
)
RETURNS SETOF train_leg_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_view.train_leg_id,
    train_leg_view.services,
    train_leg_view.calls,
    train_leg_view.stock
FROM train_leg_view
WHERE train_leg_view.train_leg_id = ANY(p_train_leg_ids);
$$;

CREATE OR REPLACE FUNCTION select_train_leg_points_by_leg_id (
    p_train_leg_id INTEGER_NOTNULL
)
RETURNS SETOF train_leg_points_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_points_view.train_leg_id,
    train_leg_points_view.train_operator_id,
    train_leg_points_view.train_brand_id,
    train_leg_points_view.call_points
FROM train_leg_points_view
WHERE train_leg_id = p_train_leg_id;
$$;

CREATE OR REPLACE FUNCTION select_train_leg_points_by_leg_ids (
    p_train_leg_ids INTEGER_NOTNULL[]
)
RETURNS SETOF train_leg_points_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_points_view.train_leg_id,
    train_leg_points_view.train_operator_id,
    train_leg_points_view.train_brand_id,
    train_leg_points_view.call_points
FROM train_leg_points_view
WHERE train_leg_id = ANY(p_train_leg_ids);
$$;

CREATE OR REPLACE FUNCTION select_train_leg_points_by_user_id (
    p_user_id INTEGER_NOTNULL,
    p_search_start TIMESTAMP WITH TIME ZONE,
    p_search_end TIMESTAMP WITH TIME ZONE
)
RETURNS SETOF train_leg_points_out_data
LANGUAGE sql
AS
$$
SELECT
    train_leg_points_view.train_leg_id,
    train_leg_points_view.train_operator_id,
    train_leg_points_view.train_brand_id,
    train_leg_points_view.call_points
FROM train_leg_points_view
INNER JOIN transport_user_train_leg
ON transport_user_train_leg.train_leg_id = train_leg_points_view.train_leg_id
WHERE transport_user_train_leg.user_id = p_user_id
AND (
    p_search_start IS NULL
    OR train_leg_points_view.first_call_time >= p_search_start
)
AND (
    p_search_end IS NULL
    OR train_leg_points_view.first_call_time <= p_search_end
)
$$;
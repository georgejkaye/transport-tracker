DROP FUNCTION IF EXISTS select_transport_user_train_leg_by_user_id;

CREATE FUNCTION select_transport_user_train_leg_by_user_id (
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
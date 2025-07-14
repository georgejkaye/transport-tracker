CREATE OR REPLACE FUNCTION select_users ()
RETURNS SETOF user_out_data
LANGUAGE sql
AS
$$
SELECT user_id, user_name, display_name, hashed_password
FROM transport_user;
$$;

CREATE OR REPLACE FUNCTION select_user_by_username (
    p_username TEXT
)
RETURNS user_out_data
LANGUAGE sql
AS
$$
SELECT (user_id, user_name, display_name, hashed_password)::user_out_data
FROM transport_user
WHERE p_username = user_name
$$;
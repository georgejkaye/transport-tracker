DROP FUNCTION IF EXISTS select_users;
DROP FUNCTION IF EXISTS select_user_by_username;

CREATE OR REPLACE FUNCTION select_users ()
RETURNS SETOF transport_user_out_data
LANGUAGE sql
AS
$$
SELECT user_id, user_name, display_name, hashed_password
FROM transport_user;
$$;

CREATE OR REPLACE FUNCTION select_user_public_data ()
RETURNS SETOF transport_user_public_out_data
LANGUAGE sql
AS
$$
SELECT user_id, user_name, display_name
FROM transport_user;
$$;

CREATE OR REPLACE FUNCTION select_user_by_username (
    p_username TEXT
)
RETURNS SETOF transport_user_out_data
LANGUAGE sql
AS
$$
SELECT user_id, user_name, display_name, hashed_password
FROM transport_user
WHERE p_username = user_name
$$;
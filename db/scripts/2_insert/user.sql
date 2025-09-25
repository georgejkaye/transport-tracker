CREATE OR REPLACE FUNCTION insert_user (
    p_username TEXT,
    p_display_name TEXT,
    p_hashed_password TEXT
) RETURNS INT
LANGUAGE sql
AS
$$
INSERT INTO transport_user (user_name, display_name, hashed_password)
VALUES (p_username, p_display_name, p_hashed_password)
RETURNING user_id;
$$;
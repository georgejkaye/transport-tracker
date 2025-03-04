CREATE OR REPLACE FUNCTION GetUsers () RETURNS SETOF UserOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN QUERY
    SELECT user_id, user_name, display_name, hashed_password
    FROM Traveller;
END;
$$;

CREATE OR REPLACE FUNCTION GetUserByUsername (
    p_username TEXT
) RETURNS UserOutData
LANGUAGE plpgsql
AS
$$
BEGIN
    RETURN (
        SELECT (user_id, user_name, display_name, hashed_password)::UserOutData
        FROM Traveller
        WHERE p_username = user_name
    );
END;
$$;
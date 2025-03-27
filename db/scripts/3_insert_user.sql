CREATE OR REPLACE FUNCTION InsertUser (
    p_username TEXT,
    p_display_name TEXT,
    p_hashed_password TEXT
) RETURNS INT
LANGUAGE plpgsql
AS
$$
DECLARE
    v_user_id INT;
BEGIN
    INSERT INTO Traveller (user_name, display_name, hashed_password)
    VALUES (p_username, p_display_name, p_hashed_password)
    RETURNING user_id INTO v_user_id;
    RETURN v_user_id;
END;
$$;
CREATE TYPE user_out_data AS (
    user_id INT,
    user_name TEXT,
    display_name TEXT,
    hashed_password TEXT
);

CREATE TYPE user_out_public_data AS (
    user_id INT,
    user_name TEXT,
    display_name TEXT
);
CREATE TYPE UserOutData AS (
    user_id INT,
    user_name TEXT,
    display_name TEXT,
    hashed_password TEXT
);

CREATE TYPE UserOutPublicData AS (
    user_id INT,
    user_name TEXT,
    display_name TEXT
);
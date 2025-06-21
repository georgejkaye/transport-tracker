CREATE TABLE traveller (
    user_id SERIAL PRIMARY KEY,
    user_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    hashed_password TEXT NOT NULL
);
CREATE TABLE Traveller (
    user_id SERIAL PRIMARY KEY,
    user_name TEXT NOT NULL,
    hashed_password TEXT NOT NULL
);
DROP TYPE IF EXISTS transport_user_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_out_public_data CASCADE;

CREATE TYPE transport_user_out_data AS (
    user_id INT,
    user_name TEXT,
    display_name TEXT,
    hashed_password TEXT
);

CREATE DOMAIN transport_user_out_data_notnull
AS transport_user_out_data NOT NULL;

CREATE TYPE transport_user_out_public_data AS (
    user_id INT,
    user_name TEXT,
    display_name TEXT
);

CREATE DOMAIN transport_user_out_public_data_notnull
AS transport_user_out_public_data NOT NULL;
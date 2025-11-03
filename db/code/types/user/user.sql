DROP DOMAIN IF EXISTS transport_user_out_data_notnull;
DROP DOMAIN IF EXISTS transport_user_public_out_data_notnull;

DROP TYPE IF EXISTS transport_user_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_public_out_data CASCADE;

CREATE TYPE transport_user_out_data AS (
    user_id INTEGER_NOTNULL,
    user_name TEXT_NOTNULL,
    display_name TEXT_NOTNULL,
    hashed_password TEXT_NOTNULL
);

CREATE DOMAIN transport_user_out_data_notnull
AS transport_user_out_data NOT NULL;

CREATE TYPE transport_user_public_out_data AS (
    user_id INTEGER_NOTNULL,
    user_name TEXT_NOTNULL,
    display_name TEXT_NOTNULL
);

CREATE DOMAIN transport_user_public_out_data_notnull
AS transport_user_public_out_data NOT NULL;
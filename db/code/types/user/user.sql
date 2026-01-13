DROP DOMAIN IF EXISTS transport_user_out_data_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_public_out_data_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_details_decimal_stat_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_details_integer_stat_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_details_interval_stat_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_details_train_out_data_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_details_out_data_notnull CASCADE;

DROP TYPE IF EXISTS transport_user_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_public_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_details_decimal_stat CASCADE;
DROP TYPE IF EXISTS transport_user_details_integer_stat CASCADE;
DROP TYPE IF EXISTS transport_user_details_interval_stat CASCADE;
DROP TYPE IF EXISTS transport_user_details_train_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_details_out_data CASCADE;

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

CREATE TYPE transport_user_details_decimal_stat AS (
    value DECIMAL_NOTNULL,
    id INTEGER_NOTNULL,
    text TEXT
);

CREATE TYPE transport_user_details_integer_stat AS (
    value INTEGER_NOTNULL,
    id INTEGER_NOTNULL,
    text TEXT
);

CREATE TYPE transport_user_details_interval_stat AS (
    value INTERVAL_NOTNULL,
    id INTEGER_NOTNULL,
    text TEXT
);

CREATE TYPE transport_user_details_train_out_data AS (
    count INTEGER_NOTNULL,
    longest_distance transport_user_details_decimal_stat,
    shortest_distance transport_user_details_decimal_stat,
    longest_duration transport_user_details_interval_stat,
    shortest_duration transport_user_details_interval_stat,
    longest_delay transport_user_details_integer_stat,
    shortest_delay transport_user_details_integer_stat,
    operator_count INTEGER_NOTNULL,
    longest_distance_operator transport_user_details_decimal_stat,
    shortest_distance_operator transport_user_details_decimal_stat,
    longest_duration_operator transport_user_details_interval_stat,
    shortest_duration_operator transport_user_details_interval_stat,
    longest_delay_operator transport_user_details_integer_stat,
    shortest_delay_operator transport_user_details_integer_stat,
    class_count INTEGER_NOTNULL,
    longest_distance_class transport_user_details_decimal_stat,
    shortest_distance_class transport_user_details_decimal_stat,
    longest_duration_class transport_user_details_interval_stat,
    shortest_duration_class transport_user_details_interval_stat,
    unit_count INTEGER_NOTNULL,
    longest_distance_unit transport_user_details_decimal_stat,
    shortest_distance_unit transport_user_details_decimal_stat,
    longest_duration_unit transport_user_details_interval_stat,
    shortest_duration_unit transport_user_details_interval_stat
);

CREATE DOMAIN transport_user_details_train_out_data_notnull
AS transport_user_details_train_out_data NOT NULL;

CREATE TYPE transport_user_details_out_data AS (
    user_id INTEGER_NOTNULL,
    user_name TEXT_NOTNULL,
    display_name TEXT_NOTNULL,
    train_stats transport_user_details_train_out_data_notnull
);

CREATE DOMAIN transport_user_details_out_data_notnull
AS transport_user_details_out_data NOT NULL;
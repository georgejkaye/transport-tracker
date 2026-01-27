DROP DOMAIN IF EXISTS transport_user_out_data_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_public_out_data_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_details_train_leg_out_data_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_details_train_year_out_data_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_details_out_data_notnull CASCADE;

DROP TYPE IF EXISTS transport_user_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_public_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_details_decimal_timestamp_stat CASCADE;
DROP TYPE IF EXISTS transport_user_details_integer_timestamp_stat CASCADE;
DROP TYPE IF EXISTS transport_user_details_interval_timestamp_stat CASCADE;
DROP TYPE IF EXISTS transport_user_details_decimal_stat CASCADE;
DROP TYPE IF EXISTS transport_user_details_integer_stat CASCADE;
DROP TYPE IF EXISTS transport_user_details_interval_stat CASCADE;
DROP TYPE IF EXISTS transport_user_details_train_leg_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_details_train_leg_year_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_details_train_station_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_details_train_station_year_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_details_train_class_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_details_train_unit_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_details_train_operator_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_details_train_year_out_data CASCADE;
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

CREATE TYPE transport_user_details_decimal_timestamp_stat AS (
    value DECIMAL_NOTNULL,
    id INTEGER_NOTNULL,
    text TEXT_NOTNULL,
    datetime TIMESTAMP_NOTNULL
);

CREATE TYPE transport_user_details_integer_timestamp_stat AS (
    value INTEGER_NOTNULL,
    id INTEGER_NOTNULL,
    text TEXT_NOTNULL,
    datetime TIMESTAMP_NOTNULL
);

CREATE TYPE transport_user_details_interval_timestamp_stat AS (
    value INTERVAL_NOTNULL,
    id INTEGER_NOTNULL,
    text TEXT_NOTNULL,
    datetime TIMESTAMP_NOTNULL
);

CREATE TYPE transport_user_details_decimal_stat AS (
    value DECIMAL_NOTNULL,
    id INTEGER_NOTNULL,
    text TEXT_NOTNULL
);

CREATE TYPE transport_user_details_integer_stat AS (
    value INTEGER_NOTNULL,
    id INTEGER_NOTNULL,
    text TEXT_NOTNULL
);

CREATE TYPE transport_user_details_interval_stat AS (
    value INTERVAL_NOTNULL,
    id INTEGER_NOTNULL,
    text TEXT_NOTNULL
);

CREATE TYPE transport_user_details_train_leg_out_data AS (
    count INTEGER_NOTNULL,
    total_distance DECIMAL_NOTNULL,
    longest_distance transport_user_details_decimal_timestamp_stat,
    shortest_distance transport_user_details_decimal_timestamp_stat,
    total_duration INTERVAL_NOTNULL,
    longest_duration transport_user_details_interval_timestamp_stat,
    shortest_duration transport_user_details_interval_timestamp_stat,
    total_delay INTEGER,
    longest_delay transport_user_details_integer_timestamp_stat,
    shortest_delay transport_user_details_integer_timestamp_stat
);

CREATE DOMAIN transport_user_details_train_leg_out_data_notnull
AS transport_user_details_train_leg_out_data NOT NULL;


CREATE TYPE transport_user_details_train_leg_year_out_data AS (
    year INTEGER,
    count BIGINT_NOTNULL,
    total_distance DECIMAL_NOTNULL,
    longest_distance transport_user_details_decimal_timestamp_stat,
    shortest_distance transport_user_details_decimal_timestamp_stat,
    total_duration INTERVAL_NOTNULL,
    longest_duration transport_user_details_interval_timestamp_stat,
    shortest_duration transport_user_details_interval_timestamp_stat,
    total_delay INTEGER,
    longest_delay transport_user_details_integer_timestamp_stat,
    shortest_delay transport_user_details_integer_timestamp_stat
);

CREATE TYPE transport_user_details_train_station_out_data AS (
    station_count INTEGER_NOTNULL,
    new_station_count INTEGER_NOTNULL,
    most_boards_and_alights_station transport_user_details_integer_stat,
    most_boards_station transport_user_details_integer_stat,
    most_alights_station transport_user_details_integer_stat,
    most_calls_station transport_user_details_integer_stat
);

CREATE TYPE transport_user_details_train_station_year_out_data AS (
    year INTEGER,
    station_count BIGINT_NOTNULL,
    new_station_count BIGINT_NOTNULL,
    most_boards_and_alights_station transport_user_details_integer_stat,
    most_boards_station transport_user_details_integer_stat,
    most_alights_station transport_user_details_integer_stat,
    most_calls_station transport_user_details_integer_stat
);

CREATE TYPE transport_user_details_train_class_out_data AS (
    class_count INTEGER_NOTNULL,
    most_count_class transport_user_details_integer_stat,
    longest_distance_class transport_user_details_decimal_stat,
    longest_duration_class transport_user_details_interval_stat
);

CREATE TYPE transport_user_details_train_unit_out_data AS (
    unit_count INTEGER_NOTNULL,
    most_count_unit transport_user_details_integer_stat,
    longest_distance_unit transport_user_details_decimal_stat,
    longest_duration_unit transport_user_details_interval_stat
);

CREATE TYPE transport_user_details_train_operator_out_data AS (
    operator_count INTEGER_NOTNULL,
    longest_distance_operator transport_user_details_decimal_stat,
    shortest_distance_operator transport_user_details_decimal_stat,
    longest_duration_operator transport_user_details_interval_stat,
    shortest_duration_operator transport_user_details_interval_stat,
    longest_delay_operator transport_user_details_integer_stat,
    shortest_delay_operator transport_user_details_integer_stat
);

CREATE TYPE transport_user_details_train_year_out_data AS (
    leg_stats_overall transport_user_details_train_leg_out_data,
    leg_stats_yearly transport_user_details_train_leg_year_out_data[],
    station_stats_overall transport_user_details_train_station_out_data,
    station_stats_yearly transport_user_details_train_station_year_out_data[]
);

CREATE DOMAIN transport_user_details_train_year_out_data_notnull
AS transport_user_details_train_year_out_data NOT NULL;

CREATE TYPE transport_user_details_out_data AS (
    user_id INTEGER_NOTNULL,
    user_name TEXT_NOTNULL,
    display_name TEXT_NOTNULL,
    train_stats transport_user_details_train_year_out_data_notnull
);

CREATE DOMAIN transport_user_details_out_data_notnull
AS transport_user_details_out_data NOT NULL;
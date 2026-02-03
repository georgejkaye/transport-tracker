DROP DOMAIN IF EXISTS transport_user_out_data_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_public_out_data_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_details_train_leg_out_data_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_details_train_leg_year_out_data_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_leg_overall_stats_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_details_train_station_out_data_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_details_train_station_year_out_data_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_station_overall_stats_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_operator_stats_notnull CASCADE;
DROP DOMAIN IF EXISTS transport_user_train_operator_year_stats_notnull CASCADE;
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
DROP TYPE IF EXISTS transport_user_details_decimal_operator_stat CASCADE;
DROP TYPE IF EXISTS transport_user_details_integer_operator_stat CASCADE;
DROP TYPE IF EXISTS transport_user_details_interval_operator_stat CASCADE;
DROP TYPE IF EXISTS transport_user_details_train_leg_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_details_train_leg_year_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_train_leg_overall_stats CASCADE;
DROP TYPE IF EXISTS transport_user_details_train_station_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_details_train_station_year_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_train_station_overall_stats CASCADE;
DROP TYPE IF EXISTS transport_user_details_train_class_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_details_train_unit_out_data CASCADE;
DROP TYPE IF EXISTS transport_user_train_operator_stats CASCADE;
DROP TYPE IF EXISTS transport_user_train_operator_year_stats CASCADE;
DROP TYPE IF EXISTS transport_user_train_operator_overall_stats CASCADE;
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

CREATE TYPE transport_user_details_decimal_operator_stat AS (
    value DECIMAL_NOTNULL,
    operator_or_brand_id INTEGER_NOTNULL,
    is_brand BOOLEAN_NOTNULL,
    operator_or_brand_name TEXT_NOTNULL
);

CREATE TYPE transport_user_details_integer_operator_stat AS (
    value INTEGER_NOTNULL,
    operator_or_brand_id INTEGER_NOTNULL,
    is_brand BOOLEAN_NOTNULL,
    operator_or_brand_name TEXT_NOTNULL
);

CREATE TYPE transport_user_details_interval_operator_stat AS (
    value INTERVAL_NOTNULL,
    operator_id INTEGER_NOTNULL,
    is_brand BOOLEAN_NOTNULL,
    operator_or_brand_name TEXT_NOTNULL
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
    year INTEGER_NOTNULL,
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

CREATE DOMAIN transport_user_details_train_leg_year_out_data_notnull
AS transport_user_details_train_leg_year_out_data NOT NULL;

CREATE TYPE transport_user_train_leg_overall_stats AS (
    overall_leg_stats transport_user_details_train_leg_out_data_notnull,
    year_leg_stats transport_user_details_train_leg_year_out_data_notnull[]
);

CREATE DOMAIN transport_user_train_leg_overall_stats_notnull
AS transport_user_train_leg_overall_stats NOT NULL;

CREATE TYPE transport_user_details_train_station_out_data AS (
    station_count INTEGER_NOTNULL,
    new_station_count INTEGER_NOTNULL,
    most_boards_and_alights_station transport_user_details_integer_stat,
    most_boards_station transport_user_details_integer_stat,
    most_alights_station transport_user_details_integer_stat,
    most_calls_station transport_user_details_integer_stat
);

CREATE DOMAIN transport_user_details_train_station_out_data_notnull
AS transport_user_details_train_station_out_data NOT NULL;

CREATE TYPE transport_user_details_train_station_year_out_data AS (
    year INTEGER_NOTNULL,
    station_count BIGINT_NOTNULL,
    new_station_count BIGINT_NOTNULL,
    most_boards_and_alights_station transport_user_details_integer_stat,
    most_boards_station transport_user_details_integer_stat,
    most_alights_station transport_user_details_integer_stat,
    most_calls_station transport_user_details_integer_stat
);

CREATE DOMAIN transport_user_details_train_station_year_out_data_notnull
AS transport_user_details_train_station_year_out_data NOT NULL;

CREATE TYPE transport_user_train_station_overall_stats AS (
    overall_station_stats transport_user_details_train_station_out_data_notnull,
    year_station_stats transport_user_details_train_station_year_out_data_notnull[]
);

CREATE DOMAIN transport_user_train_station_overall_stats_notnull
AS transport_user_train_station_overall_stats NOT NULL;

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

CREATE TYPE transport_user_train_operator_stats AS (
    operator_count INTEGER_NOTNULL,
    greatest_count transport_user_details_integer_operator_stat,
    least_count transport_user_details_integer_operator_stat,
    longest_distance transport_user_details_decimal_operator_stat,
    shortest_distance transport_user_details_decimal_operator_stat,
    longest_duration transport_user_details_interval_operator_stat,
    shortest_duration transport_user_details_interval_operator_stat,
    longest_delay transport_user_details_integer_operator_stat,
    shortest_delay transport_user_details_integer_operator_stat
);

CREATE DOMAIN transport_user_train_operator_stats_notnull
AS transport_user_train_operator_stats NOT NULL;

CREATE TYPE transport_user_train_operator_year_stats AS (
    year INTEGER_NOTNULL,
    operator_count INTEGER_NOTNULL,
    longest_distance transport_user_details_decimal_operator_stat,
    shortest_distance transport_user_details_decimal_operator_stat,
    longest_duration transport_user_details_interval_operator_stat,
    shortest_duration transport_user_details_interval_operator_stat,
    longest_delay transport_user_details_integer_operator_stat,
    shortest_delay transport_user_details_integer_operator_stat
);

CREATE DOMAIN transport_user_train_operator_year_stats_notnull
AS transport_user_train_operator_year_stats NOT NULL;

CREATE TYPE transport_user_train_operator_overall_stats AS (
    overall_operator_stats transport_user_train_operator_stats_notnull,
    year_operator_stats transport_user_train_operator_year_stats_notnull[]
);

CREATE TYPE transport_user_details_train_year_out_data AS (
    leg_stats_overall transport_user_details_train_leg_out_data,
    leg_stats_yearly transport_user_details_train_leg_year_out_data[],
    station_stats_overall transport_user_details_train_station_out_data,
    station_stats_yearly transport_user_details_train_station_year_out_data[],
    operator_stats_overall transport_user_train_operator_stats,
    operator_stats_yearly transport_user_train_operator_year_stats[]
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
DROP TYPE transport_user_train_leg_out_data CASCADE;
DROP TYPE transport_user_train_leg_operator_out_data CASCADE;
DROP TYPE transport_user_train_leg_station CASCADE;

CREATE TYPE transport_user_train_leg_station AS (
    id INTEGER,
    crs TEXT,
    name TEXT
);

CREATE TYPE transport_user_train_leg_operator_out_data AS (
    id INTEGER,
    code TEXT,
    name TEXT,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE TYPE transport_user_train_leg_out_data AS (
    id INTEGER,
    origin transport_user_train_leg_station,
    destination transport_user_train_leg_station,
    start_datetime TIMESTAMP WITH TIME ZONE,
    operator train_leg_operator_out_data,
    brand train_leg_operator_out_data,
    distance NUMERIC,
    duration INTERVAL,
    delay INTEGER
);
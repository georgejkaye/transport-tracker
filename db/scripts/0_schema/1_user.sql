CREATE TABLE transport_user (
    user_id SERIAL PRIMARY KEY,
    user_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    hashed_password TEXT NOT NULL
);

CREATE TABLE transport_user_train_leg (
    transport_user_train_leg_id SERIAL PRIMARY KEY,
    transport_user_id INTEGER NOT NULL,
    train_leg_id INTEGER NOT NULL
    FOREIGN KEY (transport_user_id) REFERENCES transport_user(user_id),
    FOREIGN KEY (train_leg_id) REFERENCES train_leg(leg_id);
);
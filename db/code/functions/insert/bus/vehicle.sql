DROP FUNCTION IF EXISTS insert_bus_models CASCADE;
DROP FUNCTION IF EXISTS insert_bus_vehicles CASCADE;
DROP FUNCTION IF EXISTS insert_bus_models_and_vehicles CASCADE;
DROP FUNCTION IF EXISTS insert_bus_vehicle CASCADE;

CREATE OR REPLACE FUNCTION insert_bus_models (
    p_models bus_model_in_data_notnull[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusModel (bus_model_name)
    SELECT v_model.model_name
    FROM UNNEST(p_models) AS v_model
    ON CONFLICT DO NOTHING;
END;
$$;

CREATE OR REPLACE FUNCTION insert_bus_vehicles (
    p_vehicles bus_vehicle_in_data_notnull[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    INSERT INTO BusVehicle (
        operator_id,
        vehicle_number,
        bustimes_id,
        numberplate,
        bus_model_id,
        livery_style,
        operator_name
    )
    SELECT
        v_vehicle.operator_id,
        v_vehicle.vehicle_number,
        v_vehicle.bustimes_id,
        v_vehicle.vehicle_numberplate,
        (SELECT bus_model_id
        FROM BusModel
        WHERE bus_model_name = v_vehicle.vehicle_model),
        v_vehicle.vehicle_livery_style,
        v_vehicle.vehicle_name
    FROM UNNEST(p_vehicles) AS v_vehicle
    ON CONFLICT DO NOTHING;
END;
$$;

CREATE OR REPLACE FUNCTION insert_bus_models_and_vehicles (
    p_models bus_model_in_data_notnull[],
    p_vehicles bus_vehicle_in_data_notnull[]
) RETURNS VOID
LANGUAGE plpgsql
AS
$$
BEGIN
    PERFORM insert_bus_models(p_models);
    PERFORM insert_bus_vehicles(p_vehicles);
END;
$$;

CREATE OR REPLACE FUNCTION insert_bus_vehicle (
    p_bus_operator_id INTEGER_NOTNULL,
    p_vehicle_identifier TEXT,
    p_bustimes_id TEXT_NOTNULL,
    p_numberplate TEXT_NOTNULL,
    p_bus_model_id INTEGER_NOTNULL,
    p_livery_style TEXT,
    p_vehicle_name TEXT
)
RETURNS insert_bus_vehicle_result
LANGUAGE sql
AS
$$
INSERT INTO busvehicle (
    bus_operator_id,
    vehicle_identifier,
    bustimes_id,
    numberplate,
    bus_model_id,
    livery_style,
    vehicle_name
)
VALUES (
    p_bus_operator_id,
    p_vehicle_identifier,
    p_bustimes_id,
    p_numberplate,
    p_bus_model_id,
    p_livery_style,
    p_vehicle_name
)
RETURNING bus_vehicle_id;
$$;
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

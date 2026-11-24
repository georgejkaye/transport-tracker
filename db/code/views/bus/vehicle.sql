DROP VIEW IF EXISTS bus_vehicle_details_view;

CREATE OR REPLACE VIEW bus_vehicle_details_view AS
SELECT
    bus_vehicle.bus_vehicle_id,
    (
        bus_operator.bus_operator_id,
        bus_operator.operator_name,
        bus_operator.national_operator_code
    )::bus_operator_summary AS vehicle_operator,
    bus_vehicle.vehicle_identifier,
    bus_vehicle.bustimes_id,
    bus_vehicle.numberplate,
    bus_model.bus_model_name,
    bus_vehicle.livery_style,
    bus_vehicle.vehicle_name
FROM bus_vehicle
INNER JOIN bus_operator
ON bus_vehicle.bus_operator_id = bus_operator.bus_operator_id
INNER JOIN bus_model
ON bus_model.bus_model_id = bus_vehicle.bus_model_id;

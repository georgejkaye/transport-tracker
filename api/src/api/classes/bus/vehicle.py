from api.db.types.bus import BusVehicleInData


def string_of_bus_vehicle_in(bus_vehicle: BusVehicleInData) -> str:
    string_brackets = f"({bus_vehicle.vehicle_numberplate}"
    if bus_vehicle.vehicle_name is not None:
        string_brackets = f"{string_brackets}/{bus_vehicle.vehicle_name}"
    string_brackets = f"{string_brackets})"
    return f"{bus_vehicle.vehicle_identifier} {string_brackets} - {bus_vehicle.vehicle_model}"

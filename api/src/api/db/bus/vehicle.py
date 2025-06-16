from psycopg import Connection

from api.classes.bus.operators import BusOperatorDetails
from api.classes.bus.vehicle import (
    BusVehicleDetails,
    BusVehicleIn,
    DbBusModelInData,
    DbBusVehicleInData,
    register_bus_vehicle_details_types,
)


def insert_bus_vehicles(
    conn: Connection, bus_vehicles: list[BusVehicleIn]
) -> None:
    bus_model_tuples: list[DbBusModelInData] = []
    bus_vehicle_tuples: list[DbBusVehicleInData] = []
    for bus_vehicle in bus_vehicles:
        bus_vehicle_model: DbBusModelInData = (bus_vehicle.model,)
        if (
            bus_vehicle.model is not None
            and bus_vehicle_model not in bus_model_tuples
        ):
            bus_model_tuples.append((bus_vehicle.model,))
        bus_vehicle_tuples.append(
            (
                bus_vehicle.operator_id,
                bus_vehicle.vehicle_number,
                bus_vehicle.bustimes_id,
                bus_vehicle.numberplate,
                bus_vehicle.model,
                bus_vehicle.livery_style,
                bus_vehicle.name,
            )
        )
    conn.execute(
        "SELECT InsertBusModelsAndVehicles(%s::BusModelInData[], %s::BusVehicleInData[])",
        [bus_model_tuples, bus_vehicle_tuples],
    )


def string_of_bus_vehicle_out(vehicle: BusVehicleDetails) -> str:
    return f"{vehicle.numberplate} ({vehicle.operator.name})"


def get_bus_vehicles_by_operator_and_id(
    conn: Connection, bus_operator: BusOperatorDetails, vehicle_number: str
) -> list[BusVehicleDetails]:
    register_bus_vehicle_details_types(conn)
    rows = conn.execute(
        "SELECT GetBusVehicles(%s, %s)", [bus_operator.id, vehicle_number]
    ).fetchall()
    return [row[0] for row in rows]


def get_bus_vehicles_by_id(
    conn: Connection, vehicle_number: str
) -> list[BusVehicleDetails]:
    register_bus_vehicle_details_types(conn)
    rows = conn.execute(
        "SELECT GetBusVehicles(NULL, %s)", [vehicle_number]
    ).fetchall()
    return [row[0] for row in rows]

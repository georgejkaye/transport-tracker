from psycopg import Connection
from psycopg.rows import class_row

from api.classes.bus.operators import BusOperatorDetails
from api.classes.bus.vehicle import (
    BusVehicleDetails,
    BusVehicleIn,
    DbBusModelInData,
    DbBusVehicleInData,
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
    with conn.cursor(row_factory=class_row(BusVehicleDetails)) as cur:
        rows = cur.execute(
            "SELECT * FROM GetBusVehicles(%s, %s)",
            [bus_operator.id, vehicle_number],
        ).fetchall()
        conn.commit()
        return rows


def get_bus_vehicles_by_id(
    conn: Connection, vehicle_number: str
) -> list[BusVehicleDetails]:
    with conn.cursor(row_factory=class_row(BusVehicleDetails)) as cur:
        rows = cur.execute(
            "SELECT * FROM GetBusVehicles(NULL, %s)", [vehicle_number]
        ).fetchall()
        conn.commit()
        return rows

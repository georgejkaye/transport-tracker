from time import sleep
from psycopg import Connection

from api.utils.database import connect, get_db_connection_data_from_args
from api.utils.interactive import information
from api.classes.bus.vehicle import BusVehicleIn
from api.pull.bus.vehicle import get_bus_operator_vehicles
from api.db.bus.vehicle import insert_bus_vehicles
from api.db.bus.operators import get_bus_operators


def populate_bus_vehicles(conn: Connection) -> None:
    information("Retrieving bus vehicles")

    operators = get_bus_operators(conn)
    all_operator_vehicles: list[BusVehicleIn] = []

    for operator in operators:
        information(f"Populating bus vehicles for {operator.name}")
        operator_vehicles = get_bus_operator_vehicles(operator)
        all_operator_vehicles = all_operator_vehicles + operator_vehicles
        sleep(1)

    information("Inserting bus vehicles")
    insert_bus_vehicles(conn, all_operator_vehicles)
    conn.commit()


if __name__ == "__main__":
    connection_data = get_db_connection_data_from_args()
    with connect(connection_data) as conn:
        populate_bus_vehicles(conn)

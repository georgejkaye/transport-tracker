import sys
from time import sleep
from api.data.bus.operators import get_bus_operators
from api.data.bus.vehicle import get_bus_operator_vehicles, insert_bus_vehicles
from api.utils.database import connect
from psycopg import Connection


def populate_bus_vehicles(conn: Connection):
    operators = get_bus_operators(conn)

    all_operator_vehicles = []

    for operator in operators:
        print(f"Getting vehicles for {operator.name}")
        operator_vehicles = get_bus_operator_vehicles(operator)
        all_operator_vehicles = all_operator_vehicles + operator_vehicles
        sleep(1)

    insert_bus_vehicles(conn, all_operator_vehicles)
    conn.commit()


if __name__ == "__main__":
    with connect(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]) as (
        conn,
        _,
    ):
        populate_bus_vehicles(conn)

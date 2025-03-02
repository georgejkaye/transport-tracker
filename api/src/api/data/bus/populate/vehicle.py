from time import sleep
from api.data.bus.operators import get_bus_operators
from api.data.bus.vehicle import get_bus_operator_vehicles, insert_bus_vehicles
from api.utils.database import connect


with connect("transport", "transport", "transport", "localhost") as (
    conn,
    _,
):
    operators = get_bus_operators(conn)

    all_operator_vehicles = []

    for operator in operators:
        print(f"Getting vehicles for {operator.name}")
        operator_vehicles = get_bus_operator_vehicles(operator)
        print(operator_vehicles)
        all_operator_vehicles = (
            all_operator_vehicles + get_bus_operator_vehicles(operator)
        )
        sleep(1)

    insert_bus_vehicles(conn, all_operator_vehicles)
    conn.commit()

from psycopg import Connection

from api.classes.interactive import PickSingle
from api.db.functions.select.bus.operator import (
    select_bus_operator_details_by_name_fetchall,
)
from api.db.functions.update.bus.leg import update_bus_leg_vehicle
from api.record.bus import get_and_insert_new_bus_vehicle_from_input
from api.utils.database import connect_with_env
from api.utils.interactive import (
    get_choice_from_input,
    get_int_from_input,
    get_text_from_input,
    print_error,
)


def main(conn: Connection) -> None:
    operator_name = get_text_from_input("Operator name", min_length=1)
    if operator_name is None:
        raise RuntimeError("Could not get operator name")
    operators = select_bus_operator_details_by_name_fetchall(
        conn, operator_name
    )
    if len(operators) == 0:
        print_error(f"No operators found for {operator_name}")
        return
    operator_choice = get_choice_from_input(
        "Operator", operators, lambda operator: operator.operator_name
    )
    match operator_choice:
        case PickSingle(bus_operator):
            pass
        case _:
            print_error("Could not get operator choice")
            return
    bus_vehicle = get_and_insert_new_bus_vehicle_from_input(
        conn, bus_operator.bus_operator_id
    )
    if bus_vehicle is None:
        print_error("Bus vehicle not inserted")
        return
    bus_leg_id = get_int_from_input("Add vehicle to bus leg", lower=0)
    if bus_leg_id is None:
        return
    update_bus_leg_vehicle(conn, bus_leg_id, bus_vehicle.bus_vehicle_id)


if __name__ == "__main__":
    with connect_with_env() as conn:
        main(conn)

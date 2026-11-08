from psycopg import Connection

from api.classes.interactive import PickSingle
from api.db.functions.insert.bus.vehicle import insert_bus_vehicle_fetchone
from api.db.functions.select.bus.model import select_bus_models_by_name_fetchall
from api.db.functions.select.bus.operator import (
    select_bus_operator_details_by_name_fetchall,
)
from api.db.functions.update.bus.leg import update_bus_leg_vehicle
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
        case PickSingle(operator):
            pass
        case _:
            print_error("Could not get operator choice")
            return
    model_search_string = get_text_from_input("Search for model", min_length=1)
    if model_search_string is None:
        raise RuntimeError("Could not get model search string")
    models = select_bus_models_by_name_fetchall(conn, model_search_string)
    model_choice = get_choice_from_input(
        "Model", models, lambda model: model.model_name
    )
    match model_choice:
        case PickSingle(model):
            pass
        case _:
            print_error("Could not get model")
            return
    vehicle_identifier = get_text_from_input("Vehicle identifier")
    numberplate = get_text_from_input("Numberplate", min_length=1)
    if numberplate is None:
        print_error("Numberplate is required")
        return
    vehicle_name = get_text_from_input("Vehicle name")
    bustimes_id = get_text_from_input("Bustimes id", min_length=1)
    if bustimes_id is None:
        print_error("Bustimes id is required")
        return
    insert_bus_vehicle_result = insert_bus_vehicle_fetchone(
        conn,
        operator.bus_operator_id,
        vehicle_identifier,
        bustimes_id,
        numberplate,
        model.bus_model_id,
        None,
        vehicle_name,
    )
    if insert_bus_vehicle_result is None:
        print_error("Bus vehicle not inserted")
        return
    bus_leg_id = get_int_from_input("Add vehicle to bus leg", lower=0)
    if bus_leg_id is None:
        return
    update_bus_leg_vehicle(
        conn, bus_leg_id, insert_bus_vehicle_result.bus_vehicle_id
    )


if __name__ == "__main__":
    with connect_with_env() as conn:
        main(conn)

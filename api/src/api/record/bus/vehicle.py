from typing import Optional

from api.db.functions.insert.bus.vehicle import insert_bus_vehicle_fetchone
from api.db.functions.select.bus.model import select_bus_models_by_name_fetchall
from api.db.functions.select.bus.vehicle import (
    select_bus_vehicle_details_by_bus_vehicle_id_fetchone,
)
from api.db.types.bus.vehicle import BusVehicleDetails
from api.utils.interactive.classes import PickSingle
from api.utils.interactive.input import (
    get_choice_from_input_paginate,
    get_text_from_input,
    print_error,
    print_information,
)
from psycopg import Connection


def get_and_insert_new_bus_vehicle_from_input(
    conn: Connection,
    bus_operator_id: int,
    vehicle_identifier: Optional[str] = None,
) -> Optional[BusVehicleDetails]:
    model_search_string = get_text_from_input("Search for model", min_length=1)
    if model_search_string is None:
        print_error("No model search string provided")
        return None
    models = select_bus_models_by_name_fetchall(conn, model_search_string)
    model_choice = get_choice_from_input_paginate(
        "Model", models, lambda model: model.model_name
    )
    match model_choice:
        case PickSingle(model):
            pass
        case _:
            print_error("Could not get model")
            return None
    vehicle_identifier = get_text_from_input(
        "Vehicle identifier", default=vehicle_identifier
    )
    numberplate = get_text_from_input("Numberplate", min_length=1)
    if numberplate is None:
        print_error("Numberplate is required")
        return None
    vehicle_name = get_text_from_input("Vehicle name")
    bustimes_id = get_text_from_input("Bustimes id", min_length=1)
    if bustimes_id is None:
        print_error("Bustimes id is required")
        return None
    insert_bus_vehicle_result = insert_bus_vehicle_fetchone(
        conn,
        bus_operator_id,
        vehicle_identifier,
        bustimes_id,
        numberplate,
        model.bus_model_id,
        None,
        vehicle_name,
    )
    if insert_bus_vehicle_result is None:
        print_error("Could not insert bus vehicle")
        return None
    print_information(
        f"Inserted bus vehicle {insert_bus_vehicle_result.bus_vehicle_id}"
    )
    return select_bus_vehicle_details_by_bus_vehicle_id_fetchone(
        conn, insert_bus_vehicle_result.bus_vehicle_id
    )

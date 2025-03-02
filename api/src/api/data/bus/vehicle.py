import operator
from api.utils.database import connect

from dataclasses import dataclass
from typing import Optional
from bs4 import BeautifulSoup
from psycopg import Connection
from slugify import slugify

from api.data.bus.operators import BusOperator, get_bus_operator_from_name
from api.utils.request import get_soup


@dataclass
class BusVehicleIn:
    operator_id: int
    operator_vehicle_id: str
    bustimes_vehicle_id: str
    numberplate: str
    model: Optional[str]
    livery_style: Optional[str]
    name: Optional[str]


def string_of_bus_vehicle_in(bus_vehicle: BusVehicleIn) -> str:
    string_brackets = f"({bus_vehicle.numberplate}"
    if bus_vehicle.name is not None:
        string_brackets = f"{string_brackets}/{bus_vehicle.name}"
    string_brackets = f"{string_brackets})"
    return f"{bus_vehicle.operator_vehicle_id} {string_brackets} - {bus_vehicle.model}"


def insert_bus_vehicles(conn: Connection, bus_vehicles: list[BusVehicleIn]):
    bus_model_tuples = []
    bus_vehicle_tuples = []
    for bus_vehicle in bus_vehicles:
        if (
            bus_vehicle.model is not None
            and bus_vehicle.model not in bus_model_tuples
        ):
            bus_model_tuples.append((bus_vehicle.model,))
        bus_vehicle_tuples.append(
            (
                bus_vehicle.operator_id,
                bus_vehicle.operator_vehicle_id,
                bus_vehicle.bustimes_vehicle_id,
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


@dataclass
class BusVehicle:
    id: int
    operator: BusOperator
    operator_vehicle_id: str
    bustimes_vehicle_id: str
    numberplate: str
    model: Optional[str]
    livery_style: Optional[str]
    name: Optional[str]


def get_bus_operator_vehicle_url(operator: BusOperator) -> str:
    operator_slug = slugify(operator.name)
    return f"https://bustimes.org/operators/{operator_slug}/vehicles"


def get_bus_operator_vehicles_page(
    operator: BusOperator,
) -> Optional[BeautifulSoup]:
    url = get_bus_operator_vehicle_url(operator)
    return get_soup(url)


bustimes_livery_css = "https://bustimes.org/liveries.1740885194.css"

livery_column_title = "Livery"
model_column_title = "Type"
name_column_title = "Name"


def get_bus_operator_vehicles(operator: BusOperator) -> list[BusVehicleIn]:
    vehicles_soup = get_bus_operator_vehicles_page(operator)
    if vehicles_soup is None:
        return []
    header_cols = vehicles_soup.select("table.fleet th")
    id_col = 0
    numberplate_col = 1
    livery_col = None
    model_col = None
    name_col = None
    current_col = 0
    for col in header_cols:
        column_title = col.text
        if column_title == livery_column_title:
            livery_col = current_col
        elif column_title == model_column_title:
            model_col = current_col
        elif column_title == name_column_title:
            name_col = current_col
        colspan = col.get("colspan")
        if isinstance(colspan, str):
            colspan_value = int(colspan)
            current_col = current_col + colspan_value
        else:
            current_col = current_col + 1
    vehicle_rows = vehicles_soup.select("table.fleet tbody tr")
    vehicles = []
    for vehicle_row in vehicle_rows:
        bustimes_id = str(vehicle_row["id"]).strip()
        vehicle_cols = vehicle_row.select("td")
        vehicle_id_col = vehicle_cols[id_col]
        vehicle_id_a = vehicle_cols[id_col].select_one("a")
        if vehicle_id_a is not None and vehicle_id_col.get("colspan") is None:
            vehicle_id = vehicle_id_a.text.strip()
            bustimes_id = str(vehicle_id_a["href"]).split("/")[-1]
            vehicle_numberplate = vehicle_cols[numberplate_col].text.strip()
            if model_col is not None:
                vehicle_model = vehicle_cols[model_col].text.strip()
            else:
                vehicle_model = None
            if name_col is not None:
                vehicle_name = vehicle_cols[name_col].text.strip()
                if vehicle_name == "":
                    vehicle_name = None
            else:
                vehicle_name = None
            vehicle_object = BusVehicleIn(
                operator.id,
                vehicle_id,
                bustimes_id,
                vehicle_numberplate,
                vehicle_model,
                None,
                vehicle_name,
            )
            vehicles.append(vehicle_object)
    return vehicles


def register_bus_vehicle(
    bus_vehicle_id: int,
    bus_operator: BusOperator,
    operator_vehicle_id: str,
    bustimes_vehicle_id: str,
    vehicle_numberplate: str,
    vehicle_model: str,
    vehicle_livery_style: Optional[str],
    vehicle_name: Optional[str],
) -> BusVehicle:
    return BusVehicle(
        bus_vehicle_id,
        bus_operator,
        operator_vehicle_id,
        bustimes_vehicle_id,
        vehicle_numberplate,
        vehicle_model,
        vehicle_livery_style,
        vehicle_name,
    )


def get_bus_vehicle_by_operator_and_id(
    conn: Connection, bus_operator: BusOperator, operator_vehicle_id: str
) -> Optional[BusVehicle]:
    rows = conn.execute(
        "SELECT GetBusVehicle(%s, %s)", [bus_operator.id, operator_vehicle_id]
    ).fetchall()
    if len(rows) > 1:
        print("Multiple vehicles found")
        return None
    if len(rows) == 0:
        print("No vehicles found")
        return None
    return rows[0][0]

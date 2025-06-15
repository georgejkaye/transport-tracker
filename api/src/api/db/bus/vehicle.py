from dataclasses import dataclass
from typing import Optional
from bs4 import BeautifulSoup
from psycopg import Connection

from api.utils.database import register_type
from api.utils.request import get_soup
from api.db.bus.operators import (
    BusOperatorDetails,
    register_bus_operator_details_types,
)


@dataclass
class BusVehicleIn:
    operator_id: int
    vehicle_number: str
    bustimes_id: str
    numberplate: str
    model: Optional[str]
    livery_style: Optional[str]
    name: Optional[str]


def string_of_bus_vehicle_in(bus_vehicle: BusVehicleIn) -> str:
    string_brackets = f"({bus_vehicle.numberplate}"
    if bus_vehicle.name is not None:
        string_brackets = f"{string_brackets}/{bus_vehicle.name}"
    string_brackets = f"{string_brackets})"
    return (
        f"{bus_vehicle.vehicle_number} {string_brackets} - {bus_vehicle.model}"
    )


DbBusModelInData = tuple[Optional[str]]
DbBusVehicleInData = tuple[
    int, str, str, str, Optional[str], Optional[str], Optional[str]
]


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


@dataclass
class BusVehicleDetails:
    id: int
    operator: BusOperatorDetails
    vehicle_number: str
    bustimes_id: str
    numberplate: str
    model: Optional[str]
    livery_style: Optional[str]
    name: Optional[str]


def register_bus_vehicle_details(
    bus_vehicle_id: int,
    bus_operator: BusOperatorDetails,
    vehicle_number: str,
    bustimes_id: str,
    vehicle_numberplate: str,
    vehicle_model: str,
    vehicle_livery_style: Optional[str],
    vehicle_name: Optional[str],
) -> BusVehicleDetails:
    return BusVehicleDetails(
        bus_vehicle_id,
        bus_operator,
        vehicle_number,
        bustimes_id,
        vehicle_numberplate,
        vehicle_model,
        vehicle_livery_style,
        vehicle_name,
    )


def register_bus_vehicle_details_types(conn: Connection) -> None:
    register_bus_operator_details_types(conn)
    register_type(conn, "BusVehicleDetails", register_bus_vehicle_details)


def string_of_bus_vehicle_out(vehicle: BusVehicleDetails) -> str:
    return f"{vehicle.numberplate} ({vehicle.operator.name})"


def get_bus_operator_url(operator: BusOperatorDetails) -> str:
    return f"https://bustimes.org/operators/{operator.national_code}"


def get_bus_operator_page(
    operator: BusOperatorDetails,
) -> Optional[BeautifulSoup]:
    url = get_bus_operator_url(operator)
    return get_soup(url)


bustimes_livery_css = "https://bustimes.org/liveries.1740885194.css"

livery_column_title = "Livery"
model_column_title = "Type"
name_column_title = "Name"


def get_bus_operator_vehicles(
    operator: BusOperatorDetails,
) -> list[BusVehicleIn]:
    operator_soup = get_bus_operator_page(operator)
    if operator_soup is None:
        return []
    tabs = operator_soup.select(".tabs li a")
    vehicle_url = None
    for tab in tabs:
        tab_text = tab.text
        if tab_text == "Vehicles":
            vehicle_url = tab["href"]
            break
    if vehicle_url is None:
        return []
    vehicles_soup = get_soup(f"https://bustimes.org{vehicle_url}")
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
    vehicles: list[BusVehicleIn] = []
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
            if livery_col is not None:
                vehicle_livery = None
            else:
                vehicle_livery = None
            vehicle_object = BusVehicleIn(
                operator.id,
                vehicle_id,
                bustimes_id,
                vehicle_numberplate,
                vehicle_model,
                vehicle_livery,
                vehicle_name,
            )
            vehicles.append(vehicle_object)
    return vehicles


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

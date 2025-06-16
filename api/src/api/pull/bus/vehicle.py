from typing import Optional
from bs4 import BeautifulSoup

from api.classes.bus.operators import BusOperatorDetails
from api.classes.bus.vehicle import BusVehicleIn
from api.utils.request import get_soup


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

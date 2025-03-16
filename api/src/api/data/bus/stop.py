from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from api.utils.database import register_type
from api.utils.request import get_soup
from bs4 import BeautifulSoup
from psycopg import Connection


@dataclass
class BusStopData:
    atco: str
    naptan: str
    common_name: str
    landmark: str
    street: str
    crossing: Optional[str]
    indicator: Optional[str]
    bearing: str
    locality: str
    parent_locality: Optional[str]
    grandparent_locality: Optional[str]
    town: Optional[str]
    suburb: Optional[str]
    latitude: Decimal
    longitude: Decimal


def insert_bus_stops(conn: Connection, bus_stops: list[BusStopData]):
    bus_stop_tuples = [
        (
            bus_stop.atco,
            bus_stop.naptan,
            bus_stop.common_name,
            bus_stop.landmark,
            bus_stop.street,
            bus_stop.crossing,
            bus_stop.indicator,
            bus_stop.bearing,
            bus_stop.locality,
            bus_stop.parent_locality,
            bus_stop.grandparent_locality,
            bus_stop.town,
            bus_stop.suburb,
            bus_stop.latitude,
            bus_stop.longitude,
        )
        for bus_stop in bus_stops
    ]
    conn.execute(
        "SELECT * FROM InsertBusStops(%s::BusStopInData[])", [bus_stop_tuples]
    )
    conn.commit()


@dataclass
class BusStop:
    id: int
    atco: str
    naptan: str
    common_name: str
    landmark: str
    street: str
    crossing: Optional[str]
    indicator: Optional[str]
    bearing: str
    locality: str
    parent_locality: Optional[str]
    grandparent_locality: Optional[str]
    town: Optional[str]
    suburb: Optional[str]
    latitude: Decimal
    longitude: Decimal


def short_string_of_bus_stop(bus_stop: BusStop) -> str:
    return f"{bus_stop.atco}: {bus_stop.common_name} ({bus_stop.indicator}), {bus_stop.locality}"


def register_bus_stop(
    id: int,
    atco: str,
    naptan: str,
    common_name: str,
    landmark: str,
    street: str,
    crossing: Optional[str],
    indicator: Optional[str],
    bearing: str,
    locality: str,
    parent_locality: Optional[str],
    grandparent_locality: Optional[str],
    town: Optional[str],
    suburb: Optional[str],
    latitude: float,
    longitude: float,
) -> BusStop:
    return BusStop(
        id,
        atco,
        naptan,
        common_name,
        landmark,
        street,
        crossing,
        indicator,
        bearing,
        locality,
        parent_locality,
        grandparent_locality,
        town,
        suburb,
        Decimal(latitude),
        Decimal(longitude),
    )


def get_bus_stops(conn: Connection, search_string: str) -> list[BusStop]:
    register_type(conn, "BusStopOutData", register_bus_stop)
    rows = conn.execute("SELECT GetBusStops(%s)", [search_string]).fetchall()
    return [row[0] for row in rows]


def get_bus_stops_from_atcos(
    conn: Connection, atcos: list[str]
) -> dict[str, BusStop]:
    register_type(conn, "BusStopOutData", register_bus_stop)
    rows = conn.execute("SELECT GetBusStopsFromAtcos(%s)", [atcos])
    atco_bus_stop_dict = {}
    for row in rows:
        bus_stop = row[0]
        atco_bus_stop_dict[bus_stop.atco] = bus_stop
    return atco_bus_stop_dict


def get_bus_stop_page_url(
    bus_stop: BusStop, search_datetime: datetime = datetime.now()
) -> str:
    return (
        f"https://bustimes.org/stops/{bus_stop.atco}"
        + f"?date={search_datetime.strftime("%Y-%m-%d")}"
        + f"&time={search_datetime.strftime("%H:%M")}"
    )


def get_bus_stop_page(
    bus_stop: BusStop, search_datetime: datetime = datetime.now()
) -> Optional[BeautifulSoup]:
    url = get_bus_stop_page_url(bus_stop, search_datetime)
    soup = get_soup(url)
    return soup


@dataclass
class BusStopDeparture:
    service: str
    destination: str
    dep_time: datetime
    bustimes_journey_id: int


def short_string_of_bus_stop_departure(departure: BusStopDeparture) -> str:
    return f"{departure.dep_time.strftime("%H:%M")}: {departure.service} to {departure.destination}"


def get_departures_from_bus_stop_soup(
    soup: BeautifulSoup,
) -> list[BusStopDeparture]:
    departure_input_boxes = soup.select("#departures input")
    if len(departure_input_boxes) == 0:
        return []
    search_date_value = datetime.strptime(
        str(departure_input_boxes[0]["value"]), "%Y-%m-%d"
    )
    search_time_value = datetime.strptime(
        str(departure_input_boxes[1]["value"]), "%H:%M"
    )
    departures_tables = soup.select("#departures > table")
    departures = []
    for i, departure_table in enumerate(departures_tables):
        current_date = search_date_value + timedelta(days=i)
        departure_rows = departure_table.find_all("tr")
        for departure_row in departure_rows[1:]:
            departure_data = departure_row.find_all("td")
            departure_service = departure_data[0].find("a").text.strip()
            departure_destination = departure_data[1].text.strip()
            departure_time_data = departure_data[2]
            departure_time = datetime.strptime(
                departure_time_data.find("a").text.strip(), "%H:%M"
            )
            departure_datetime = datetime(
                current_date.year,
                current_date.month,
                current_date.day,
                departure_time.hour,
                departure_time.minute,
                0,
            )
            departure_bustimes_journey_id = int(
                departure_time_data.find("a")["href"].split("/")[2]
            )
            departure = BusStopDeparture(
                departure_service,
                departure_destination,
                departure_datetime,
                departure_bustimes_journey_id,
            )
            departures.append(departure)
    return departures


def get_departures_from_bus_stop(
    bus_stop: BusStop, search_datetime: datetime
) -> list[BusStopDeparture]:
    soup = get_bus_stop_page(bus_stop, search_datetime)
    if soup is None:
        return []
    return get_departures_from_bus_stop_soup(soup)

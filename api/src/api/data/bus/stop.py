from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from re import search
from typing import Optional
from api.utils.database import connect, register_type
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
    print(bus_stops[0])
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
        "SELECT * FROM InsertBusStops(%s::BusStopData[])", [bus_stop_tuples]
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
    return f"{bus_stop.common_name} ({bus_stop.indicator}), {bus_stop.locality}"


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


def get_bus_stop_page_url(
    bus_stop: BusStop, search_datetime: datetime = datetime.now()
) -> str:
    return (
        f"https://bustimes.org/stops/{bus_stop.atco}"
        + f"?date={search_datetime.strftime("%Y-%m-%d")}"
        + f"&time={search_datetime.strftime("%H%3A%M")}"
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
    service_url: str


def get_departures_from_bus_stop_soup(
    soup: BeautifulSoup,
) -> list[BusStopDeparture]:
    departures_tables = soup.select("#departures > table")
    departures = []
    for departure_table in departures_tables:
        departure_rows = departure_table.find_all("tr")
        for departure_row in departure_rows[1:]:
            departure_data = departure_row.find_all("td")
            departure_service = departure_data[0].find("a").text.strip()
            departure_destination = departure_data[1].text.strip()
            departure_time_data = departure_data[2]
            departure_time = datetime.strptime(
                departure_time_data.find("a").text.strip(), "%H:%M"
            )
            departure_url = departure_time_data.find("a")["href"]
            departure = BusStopDeparture(
                departure_service,
                departure_destination,
                departure_time,
                departure_url,
            )
            departures.append(departure)
    return departures

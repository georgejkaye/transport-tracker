from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from psycopg import Connection

from api.utils.database import register_type


@dataclass
class BusStopData:
    atco: str
    naptan: str
    common_name: str
    landmark: Optional[str]
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


@dataclass
class BusStopDeparture:
    service: str
    destination: str
    dep_time: datetime
    bustimes_journey_id: int


def short_string_of_bus_stop_departure(departure: BusStopDeparture) -> str:
    return f"{departure.dep_time.strftime("%H:%M")}: {departure.service} to {departure.destination}"


@dataclass
class BusStopDetails:
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


def short_string_of_bus_stop_details(bus_stop: BusStopDetails) -> str:
    if bus_stop.indicator is None:
        indicator_text = ""
    else:
        indicator_text = f" ({bus_stop.indicator})"
    return f"{bus_stop.common_name}{indicator_text}, {bus_stop.locality} ({bus_stop.atco})"


def register_bus_stop_details(
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
) -> BusStopDetails:
    return BusStopDetails(
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


def register_bus_stop_details_types(conn: Connection) -> None:
    register_type(conn, "BusStopDetails", register_bus_stop_details)

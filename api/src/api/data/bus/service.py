from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from api.data.bus.operators import BusOperator, get_operator_from_name
from api.data.bus.stop import BusStop
from api.utils.request import get_soup
from bs4 import BeautifulSoup
from psycopg import Connection


@dataclass
class BusService:
    id: int
    operator: BusOperator
    line: str
    outbound: str
    inbound: str
    bg_colour: Optional[str]
    fg_colour: Optional[str]


@dataclass
class BusCall:
    id: int
    stop: BusStop
    plan_arr: datetime
    plan_dep: datetime


@dataclass
class BusJourney:
    id: int
    service: BusService
    calls: list[BusCall]


@dataclass
class BusLeg:
    id: int
    journey: BusJourney
    calls: list[BusCall]


def get_bus_journey_url(bustimes_journey_id: int) -> str:
    return f"https://bustimes.org/trips/{bustimes_journey_id}"


def get_bus_journey_page(bustimes_journey_id: int) -> Optional[BeautifulSoup]:
    url = get_bus_journey_url(bustimes_journey_id)
    return get_soup(url)


def get_bus_journey(
    conn: Connection, bustimes_journey_id: int
) -> Optional[BusJourney]:
    soup = get_bus_journey_page(bustimes_journey_id)
    if soup is None:
        return soup

    breadcrumbs = soup.select(".breadcrumb > li")
    operator_name = breadcrumbs[0].text
    operator = get_operator_from_name(conn, operator_name)

    if operator is None:
        return None

    service_line_name = breadcrumbs[1].text

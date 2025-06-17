from datetime import datetime, timedelta
from typing import Optional

from bs4 import BeautifulSoup, Tag

from api.classes.bus.stop import BusStopDeparture, BusStopDetails
from api.utils.request import get_soup


def get_bus_stop_page_url(
    bus_stop: BusStopDetails, search_datetime: datetime = datetime.now()
) -> str:
    return (
        f"https://bustimes.org/stops/{bus_stop.atco}"
        + f"?date={search_datetime.strftime("%Y-%m-%d")}"
        + f"&time={search_datetime.strftime("%H:%M")}"
    )


def get_bus_stop_page(
    bus_stop: BusStopDetails, search_datetime: datetime = datetime.now()
) -> Optional[BeautifulSoup]:
    url = get_bus_stop_page_url(bus_stop, search_datetime)
    soup = get_soup(url)
    return soup


def get_departures_from_bus_stop_soup(
    soup: BeautifulSoup, datetime_offset: timedelta
) -> list[BusStopDeparture]:
    departure_input_boxes = soup.select("#departures input")
    if len(departure_input_boxes) == 0:
        return []
    search_date_value = (
        datetime.strptime(str(departure_input_boxes[0]["value"]), "%Y-%m-%d")
        - datetime_offset
    )
    departures_tables = soup.select("#departures > table")
    departures: list[BusStopDeparture] = []
    for i, departure_table in enumerate(departures_tables):
        current_date = search_date_value + timedelta(days=i)
        departure_rows = departure_table.find_all("tr")
        for departure_row in departure_rows[1:]:
            if not isinstance(departure_row, Tag):
                continue
            departure_data = departure_row.find_all("td")
            departure_service_td = departure_data[0]
            if not isinstance(departure_service_td, Tag):
                continue
            departure_service_a = departure_service_td.find("a")
            if not isinstance(departure_service_a, Tag):
                continue
            departure_service = departure_service_a.text.strip()
            departure_destination_td = departure_data[1]
            departure_destination = departure_destination_td.text.strip()
            departure_time_td = departure_data[2]
            if not isinstance(departure_time_td, Tag):
                continue
            departure_time_a = departure_time_td.find("a")
            if not isinstance(departure_time_a, Tag):
                continue
            departure_time = datetime.strptime(
                departure_time_a.text.strip(), "%H:%M"
            )
            departure_datetime = datetime(
                current_date.year,
                current_date.month,
                current_date.day,
                departure_time.hour,
                departure_time.minute,
                0,
            )
            departure_time_a_href = departure_time_a["href"]
            if not isinstance(departure_time_a_href, str):
                continue
            departure_bustimes_journey_id = int(
                departure_time_a_href.split("/")[2]
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
    bus_stop: BusStopDetails,
    search_datetime: datetime,
    datetime_offset: timedelta,
) -> list[BusStopDeparture]:
    soup = get_bus_stop_page(bus_stop, search_datetime)
    if soup is None:
        return []
    return get_departures_from_bus_stop_soup(soup, datetime_offset)

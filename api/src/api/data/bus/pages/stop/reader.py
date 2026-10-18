from datetime import datetime, timedelta
from typing import Optional

from api.data.bus.pages.stop.classes import BusStopDeparture
from api.data.bus.stop import BusStopDetails
from api.data.selenium.driver import Driver
from bs4 import BeautifulSoup


def get_bus_stop_page_url(
    bus_stop: BusStopDetails, search_datetime: datetime = datetime.now()
) -> str:
    return (
        f"https://bustimes.org/stops/{bus_stop.atco}"
        + f"?date={search_datetime.strftime('%Y-%m-%d')}"
        + f"&time={search_datetime.strftime('%H:%M')}"
    )


def get_bus_stop_page(
    driver: Driver, bus_stop: BusStopDetails, search_datetime: datetime = datetime.now()
) -> Optional[BeautifulSoup]:
    return driver.get_page_html(get_bus_stop_page_url(bus_stop, search_datetime))


def short_string_of_bus_stop_departure(departure: BusStopDeparture) -> str:
    return f"{departure.dep_time.strftime('%H:%M')}: {departure.service} to {departure.destination}"


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
        departure_rows = departure_table.select("tr")
        for departure_row in departure_rows[1:]:
            departure_data = departure_row.select("td")
            departure_service_a = departure_data[0].select_one("a")
            if departure_service_a is None:
                continue
            departure_service = departure_service_a.text.strip()
            departure_destination = departure_data[1].text.strip().split("\n")[0]
            departure_time_data = departure_data[2]
            departure_time_a = departure_time_data.select_one("a")
            if departure_time_a is None:
                continue
            departure_time = datetime.strptime(departure_time_a.text.strip(), "%H:%M")
            departure_datetime = datetime(
                current_date.year,
                current_date.month,
                current_date.day,
                departure_time.hour,
                departure_time.minute,
                0,
            )
            departure_time_date_a_href = departure_time_a.get("href")
            if departure_time_date_a_href is None or not isinstance(
                departure_time_date_a_href, str
            ):
                continue
            if "trips" in departure_time_date_a_href:
                live = False
            elif "journeys" in departure_time_date_a_href:
                live = True
            else:
                continue
            departure_bustimes_id = int(departure_time_date_a_href.split("/")[2])
            departure = BusStopDeparture(
                live,
                departure_service,
                departure_destination,
                departure_datetime,
                departure_bustimes_id,
            )
            departures.append(departure)
    return departures


def get_departures_from_bus_stop(
    driver: Driver,
    bus_stop: BusStopDetails,
    search_datetime: datetime,
    datetime_offset: timedelta,
) -> list[BusStopDeparture]:
    soup = get_bus_stop_page(driver, bus_stop, search_datetime)
    if soup is None:
        return []
    return get_departures_from_bus_stop_soup(soup, datetime_offset)

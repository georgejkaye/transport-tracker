
import re
from bs4 import BeautifulSoup
from network import get_station_crs_from_name

from structures import Mileage, Service


def get_location_div(soup: BeautifulSoup, crs: str) -> BeautifulSoup:
    calls = soup.find_all(class_="call")
    for call in calls:
        if crs in call.get_text():
            return call


def get_miles_and_chains(div: BeautifulSoup) -> Mileage:
    miles = div.find(class_="miles")
    chains = div.find(class_="chains")
    return Mileage(int(miles.get_text()), int(chains.get_text()))


single_alloc_regex = r"Operated with ([0-9 \+]*)"
multi_alloc_regex = r"([0-9 \+]*) to ([A-Za-z ]*)"


def get_allocation(service: Service, origin: str, destination: str) -> list[tuple[list[int], tuple[str, str]]]:
    soup = service.page
    alloc_div = soup.find(class_="allocation")
    alloc_lis = alloc_div.find_all("li")
    if len(allocs) == 0:
        alloc_span = alloc_div.find("span")
        result = re.search(single_alloc_regex, alloc_span.get_text())
        allocs = [(result.group(1), service.origins[0].crs,
                   service.destinations[0].crs)]
    else:
        previous = service.origins[0].crs
        allocs = []
        for alloc in alloc_lis:
            result = re.search(multi_alloc_regex, alloc)
            units = result.group(1)
            until = get_station_crs_from_name(result.group(2))
            allocs.append((
                units,
                previous,
                until
            ))
            previous = until
    return allocs


def get_mileage_for_service_call(service: Service, crs: str) -> Mileage:
    div = get_location_div(service.page, crs)
    return get_miles_and_chains(div)

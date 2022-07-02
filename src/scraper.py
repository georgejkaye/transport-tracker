import requests

from datetime import date
from bs4 import BeautifulSoup
from debug import error_msg

from structures import Mileage, Service


def soupify(doc: str) -> BeautifulSoup:
    return BeautifulSoup(doc, "html.parser")


def get_service_page_url(date: date, id: str) -> str:
    date_string = date.strftime("%Y-%m-%d")
    return f"https://www.realtimetrains.co.uk/service/gb-nr:{id}/{date_string}/detailed"


def get_service_page(date: date, id: str) -> BeautifulSoup:
    url = get_service_page_url(date, id)
    page = requests.get(url)
    if (page.status_code != 200):
        error_msg(f"Request {url} failed: {page.status_code}")
        exit(1)

    html_doc = page.text
    return soupify(html_doc)


def get_location_div(soup: BeautifulSoup, crs: str) -> BeautifulSoup:
    calls = soup.find_all(class_="call")
    for call in calls:
        if crs in call.get_text():
            return call


def get_miles_and_chains(div: BeautifulSoup) -> Mileage:
    miles = div.find(class_="miles")
    chains = div.find(class_="chains")
    return Mileage(int(miles.get_text()), int(chains.get_text()))


def get_mileage_for_service_call(service: Service, crs: str) -> Mileage:
    soup = get_service_page(service.date, service.uid)
    div = get_location_div(soup, crs)
    return get_miles_and_chains(div)

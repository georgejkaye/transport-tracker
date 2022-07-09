import requests

from datetime import date
from bs4 import BeautifulSoup  # type: ignore
from debug import error_msg


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

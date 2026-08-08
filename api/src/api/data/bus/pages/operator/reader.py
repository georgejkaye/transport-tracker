from typing import Optional

from api.data.bus.pages.bustimes import accept_bustimes_cookies
from api.data.bus.pages.operator.classes import BustimesOperator
from api.data.selenium.driver import Driver
from api.utils.interactive import information
from undetected_geckodriver import Firefox


def get_bustimes_operator_url(slug: str) -> str:
    return f"https://bustimes.org/operators/{slug}"


def setup_bustimes_operator_page(driver: Firefox):
    accept_bustimes_cookies(driver)


def get_bustimes_operator(driver: Driver, slug: str) -> Optional[BustimesOperator]:
    url = get_bustimes_operator_url(slug)
    page_soup = driver.get_page_html(url, setup_bustimes_operator_page)
    name = page_soup.select_one("h1")
    if name is None:
        information(f"Could not find operator name on {url}")
        return None
    details = page_soup.select_one('div[id="content"] > div:last-child')
    if details is None:
        information(f"Could not find operator details on {details}")
        return None
    noc = details.select_one("div :last-child > dd")
    if noc is None:
        information(f"Could not find national operator code on {details}")
        return None
    return BustimesOperator(name.text, noc.text)

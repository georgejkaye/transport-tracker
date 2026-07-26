from typing import Optional

from api.data.bus.pages.operator.classes import BustimesOperator
from api.utils.interactive import information
from api.utils.request import get_soup


def get_bustimes_operator_url(slug: str) -> str:
    return f"https://bustimes.org/operators/{slug}"


def get_bustimes_operator(slug: str) -> Optional[BustimesOperator]:
    url = get_bustimes_operator_url(slug)
    page_soup = get_soup(url)
    if page_soup is None:
        information(f"Could not get operator page {url}")
        return None
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

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from api.utils.mileage import miles_and_chains_to_miles
from api.utils.request import get_soup
from api.utils.times import make_timezone_aware
from bs4 import BeautifulSoup, Tag


def get_service_page_url(id: str, service_date: datetime) -> str:
    date_string = service_date.strftime("%Y-%m-%d")
    return f"https://www.realtimetrains.co.uk/service/gb-nr:{id}/{date_string}/detailed"


def get_train_service_soup(
    service_id: str, run_date: datetime
) -> Optional[BeautifulSoup]:
    url = get_service_page_url(service_id, run_date)
    soup = get_soup(url)
    return soup


def get_location_div_from_service_page(
    service_soup: BeautifulSoup,
    crs: str,
    plan_arr: Optional[datetime],
    plan_dep: Optional[datetime],
) -> Optional[Tag]:
    calls = service_soup.find_all(class_="call")
    for call in calls:
        if isinstance(call, Tag):
            location = call.find(".location")
            gbtt_arr = call.find(".gbtt .arr")
            gbtt_dep = call.find(".gbtt .dep")

            if (
                not isinstance(location, Tag)
                or crs.upper() not in location.get_text()
            ):
                continue

            if plan_arr is not None:
                if (
                    not isinstance(gbtt_arr, Tag)
                    or plan_arr.strftime("%H%M") != gbtt_arr.get_text()
                ):
                    continue

            if plan_dep is not None:
                if (
                    not isinstance(gbtt_dep, Tag)
                    or plan_dep.strftime("%H%M") != gbtt_dep.get_text()
                ):
                    continue

            return call
    return None


def get_miles_and_chains_from_call_div(
    call_div_soup: Tag,
) -> Optional[Decimal]:
    miles = call_div_soup.find(class_="miles")
    chains = call_div_soup.find(class_="chains")
    if miles is None or chains is None:
        return None
    miles_text = miles.get_text()
    miles_int = int(miles_text)
    chains_text = chains.get_text()
    chains_int = int(chains_text)
    return miles_and_chains_to_miles(miles_int, chains_int)


def get_call_mileage_from_service_soup(
    service_soup: BeautifulSoup,
    station_crs: str,
    plan_arr: Optional[datetime],
    plan_dep: Optional[datetime],
) -> Optional[Decimal]:
    call_div = get_location_div_from_service_page(
        service_soup, station_crs, plan_arr, plan_dep
    )
    return (
        get_miles_and_chains_from_call_div(call_div)
        if call_div is not None
        else None
    )

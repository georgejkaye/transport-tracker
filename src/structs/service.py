import re

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup  # type: ignore
from api import Credentials, request_service
from debug import debug_msg
from structs.location import Location, Mileage, ShortLocation
from network import get_station_crs_from_name, lnwr_dests
from record import make_planact_entry
from scraper import get_service_page
from structures import PlanActTime
from times import make_planact


@dataclass
class Allocation:
    stock: list[int]
    until: Optional[str]


def get_allocations(html: BeautifulSoup) -> list[Allocation]:
    allocation_div = html.find(class_="allocation")

    if allocation_div is not None:

        lis = allocation_div.find_all("li")

        if len(lis) == 0:
            units = list(map(lambda x: int(x), allocation_div.find(
                "span").get_text().split(" + ")))
            allocation = Allocation(units, None)
            allocations = [allocation]
        else:
            allocations = []
            for li in lis:
                allocation_regex = r"([0-9+ ]*) to ([A-Za-z]*)"
                matches = re.search(allocation_regex, li.get_text())

                if matches is not None:
                    units = matches.group(1)
                    split = units.split(" + ")
                    unit_nos = list(map(lambda x: int(x), split))
                    until = matches.group(2)
                    allocations.append(Allocation(
                        unit_nos, get_station_crs_from_name(until)))
                else:
                    debug_msg("Allocation div exists but no allocation")
                    exit(1)

        return allocations
    else:
        return []


def get_service_url(uid: str, service_date: date) -> str:
    date_string = service_date.strftime("%Y-%m-%d")
    return f"https://www.realtimetrains.co.uk/service/gb-nr:{uid}/{date_string}/detailed"


@ dataclass
class Service:
    uid: str
    date: date
    headcode: str
    origins: list[ShortLocation]
    destinations: list[ShortLocation]
    power: str
    toc_code: str
    toc: str
    calls: list[tuple[Allocation, list[Location]]]
    service_url: str


def get_toc(origins: list[ShortLocation], destinations: list[ShortLocation], toc: str) -> str:
    # RTT abbreviates LNER so we expand it
    if toc == "LNER":
        toc = "London North Eastern Railway"
    # The official toc for West Midlands Railway and London North Western Railway
    # is West Midlands Trains', but we want to use the former 'brand names'
    if toc == "West Midlands Trains":
        lnwr = False
        for loc in origins:
            if loc.crs in lnwr_dests:
                lnwr = True
                break
        for loc in destinations:
            if loc.crs in lnwr_dests:
                lnwr = True
                break
        if lnwr:
            toc = "London Northwestern Railway"
        else:
            toc = "West Midlands Railway"
    return toc


def get_mileages(html: BeautifulSoup) -> Dict[str, Mileage]:
    calls = html.find_all(class_="call")
    mileages: Dict[str, Mileage] = {}
    for call in calls:
        location = call.find(class_="name")
        crs = location.get_text().split(" ")[-1]
        miles = call.find(class_="miles")
        chains = call.find(class_="chains")
        mileages[crs[1:-1]] = Mileage(miles, chains)
    return mileages


def get_calls(date: date, calls: list[Dict[str, Any]], allocations: list[Allocation], mileage_map: Dict[str, Mileage]) -> tuple[list[tuple[Allocation, list[Location]]], list[tuple[str, str]]]:
    splits = []
    formations = []
    current_formation = []
    if len(allocations) != 0:
        allocation = allocations.pop(0)
    else:
        allocation = None
    for i, call in enumerate(calls):
        call_name = call["description"]
        call_crs = call["crs"]
        call_tiploc = call["tiploc"]
        platform = call.get("platform")

        if i != 0:
            arr = make_planact(
                date, call["gbttBookedArrival"], call.get("realtimeArrival"))
        else:
            arr = None

        if i != len(calls) - 1:
            dep = make_planact(
                date, call["gbttBookedDeparture"], call.get("realtimeDeparture"))
        else:
            dep = None

        location = Location(
            call_name,
            call_crs,
            call_tiploc,
            arr,
            dep,
            platform,
            mileage_map[call_crs]
        )

        current_formation.append(location)

        if allocation is not None and len(allocations) != 0 and call_crs == allocation.until:
            formations.append((allocation, current_formation))
            allocation = allocations.pop(0)
            current_formation = [location]

        # Check for if the service divides
        associations = call.get("associations")
        if associations is not None:
            for assoc in associations:
                assoc_type = assoc.get("type")
                if assoc_type == "divide":
                    splits.append((assoc.get("associatedUid"),
                                  assoc.get("associatedRundate")))

    formations.append((allocation, current_formation))

    return (formations, splits)


def make_services(uid: str, service_date: date, credentials: Credentials) -> list[Service]:
    service_json = request_service(uid, service_date, credentials)

    def map_short_locations(short_locs: list[Dict[str, Any]]) -> list[ShortLocation]:
        return list(map(
            lambda loc:
                ShortLocation(
                    loc["description"],
                    get_station_crs_from_name(loc["description"]),
                    loc["tiploc"]
                ), short_locs))

    service_uid = service_json["serviceUid"]
    url = get_service_url(service_uid, service_date)
    html = get_service_page(service_date, service_uid)
    headcode = service_json["trainIdentity"]
    origins = map_short_locations(service_json["origin"])
    destinations = map_short_locations(service_json["destination"])
    power = service_json["powerType"]
    toc_code = service_json["atocCode"]
    toc = get_toc(origins, destinations, service_json["atocName"])
    allocations = get_allocations(html)
    mileages = get_mileages(html)
    (calls, other_services) = get_calls(
        service_date, service_json["locations"], allocations, mileages)

    service = Service(
        service_uid,
        service_date,
        headcode,
        origins,
        destinations,
        power,
        toc_code,
        toc,
        calls,
        url
    )

    print(service)

    return [service]

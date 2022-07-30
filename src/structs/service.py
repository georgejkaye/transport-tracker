import re

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup  # type: ignore
from api import Credentials, request_service
from debug import debug_msg
from structs.network import Network, get_station_crs_from_name
from scraper import get_service_page
from structs.time import PlanActTime, make_planact


@dataclass
class Allocation:
    stock: list[int]
    until: Optional[str]


def get_allocation_list(units: str) -> list[int]:
    return list(map(lambda x: int(x), units.split(" + ")))


def get_allocation(text: str, network: Network) -> Allocation:
    allocation_regex = r"([0-9+ ]*) to ([A-Za-z ]*)"
    matches = re.search(allocation_regex, text)
    if matches is not None:
        unit_match = matches.group(1)
        units = get_allocation_list(unit_match)
        until = matches.group(2)
        allocation = Allocation(
            units, get_station_crs_from_name(network, until))
        return allocation


def get_allocations(html: BeautifulSoup, network: Network) -> list[Allocation]:
    allocation_div = html.find(class_="allocation")
    # Some units don't have allocation info yet
    if allocation_div is not None:
        lis = allocation_div.find_all("li")
        # If a service only has one allocation for its duration there
        # will be no lis
        if len(lis) == 0:
            allocation_text = allocation_div.find("span").get_text()
            allocation = get_allocation(allocation_text, network)
            allocations = [allocation]
        else:
            allocations = []
            for li in lis:
                allocation_text = li.get_text()
                allocation = get_allocation(allocation_text, network)
                # Safety check!
                allocations.append(allocation)
        return allocations
    else:
        return []


@dataclass
class Mileage:
    miles: Optional[int]
    chains: Optional[int]


@dataclass
class ShortLocation:
    name: str
    crs: str
    time: time


def get_multiple_location_string(locs: list[ShortLocation]) -> str:
    for i, loc in enumerate(locs):
        if i == 0:
            string = loc.name
        else:
            string = string + " and " + loc.name
    return string


@dataclass
class AssociatedService:
    """
    An associated refers to a service that splits off another one
    """
    uid: str
    service_date: date


@dataclass
class Location:
    name: str
    crs: str
    tiploc: str
    arr: Optional[PlanActTime]
    dep: Optional[PlanActTime]
    platform: Optional[str]
    mileage: Optional[Mileage]
    split: list['Service']


@dataclass
class Station:
    name: str
    crs: str
    around_time: datetime
    tiploc: str
    services: list['Service']


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
    calls: list[tuple[Optional[Allocation], list[Location]]]
    service_url: str


def get_toc(origins: list[ShortLocation], destinations: list[ShortLocation], toc: str, network: Network) -> str:
    # RTT abbreviates LNER so we expand it
    if toc == "LNER":
        toc = "London North Eastern Railway"
    # The official toc for West Midlands Railway and London North Western Railway
    # is West Midlands Trains', but we want to use the 'brand names'
    if toc == "West Midlands Trains":
        lnwr = False
        for loc in origins:
            if loc.crs in network.lnwr_destinations:
                lnwr = True
                break
        for loc in destinations:
            if loc.crs in network.lnwr_destinations:
                lnwr = True
                break
        if lnwr:
            toc = "London Northwestern Railway"
        else:
            toc = "West Midlands Railway"
    return toc


def get_mileages(html: BeautifulSoup) -> Dict[str, Optional[Mileage]]:
    calls = html.find_all(class_="call")
    mileages: Dict[str, Optional[Mileage]] = {}
    for call in calls:
        location = call.find(class_="name")
        location_text = location.get_text()
        # Check if this call is actually a station call
        # If it is, it'll have a [TLC]
        if location_text[-1] != "]":
            continue
        # Extract the actual CRS
        crs = location.get_text().split(" ")[-1][1: -1]
        miles = call.find(class_="miles")
        # Not all services have mileages given
        # If this one doesn't, we just input None
        if miles is None:
            mileages[crs] = None
        else:
            chains = call.find(class_="chains")
            mileages[crs] = Mileage(miles, chains)
    return mileages


"""
An allocation list is a list of tuples (allocation, locations), where
allocation is a (possibly None) Allocation object, and locations is a
list of Location objects that this allocation is used for
"""
AllocationList = list[tuple[Optional[Allocation], list[Location]]]


def get_divisions(call: Dict[str, Any], credentials:  Credentials, network: Network) -> list[Service]:
    """
    Given a call, get the list of services that divide off at it
    """
    dividing_services = []
    associations = call.get("associations")
    if associations is not None:
        for association in associations:
            association_type = association.get("type")
            if association_type == "divide":
                association_uid = association["associatedUid"]
                association_date = datetime.strptime(
                    association["associatedRunDate"], "%Y-%m-%d").date()
                associated_service = make_service(
                    association_uid, association_date, credentials, network)
                dividing_services.append(associated_service)
        return dividing_services
    return []


def get_calls(date: date, json: Dict[str, Any], credentials: Credentials, network: Network) -> tuple[AllocationList, list[AssociatedService]]:
    """
    Get a list of all the calls this service makes, with the associated allocations if available
    Also returns the list of associated services if any
    """

    html = get_service_page(date, json["serviceUid"])
    allocations = get_allocations(html, network)
    mileage_map = get_mileages(html)
    calls = json["locations"]

    division_services: list[AssociatedService] = []
    formations: list[tuple[Optional[Allocation], list[Location]]] = []
    locations_with_current_formation: list[Location] = []
    # Allocation details might be unavailable. If they are,
    # just set the allocation to None and move on
    if len(allocations) != 0:
        current_formation = allocations.pop(0)
    else:
        current_formation = None
    for i, call in enumerate(calls):
        call_name = call["description"]
        call_crs = call["crs"]
        call_tiploc = call["tiploc"]
        platform = call.get("platform")
        # No arrival for first call
        if i != 0:
            arr = make_planact(
                date, call.get("gbttBookedArrival"), call.get("realtimeArrival"))
        else:
            arr = None
        # No departure for final call
        if i != len(calls) - 1:
            dep = make_planact(
                date, call.get("gbttBookedDeparture"), call.get("realtimeDeparture"))
        else:
            dep = None
        # Check if we have reached a call at which the service divides
        # If this is the first call, we skip it, because if this service
        # divides off another then the same association is used, and a
        # service can't divide at the first stop anyway
        if i != 0:
            divisions_at_this_call = get_divisions(call, credentials, network)
        else:
            divisions_at_this_call = []
        # Make the location object
        location = Location(
            call_name,
            call_crs,
            call_tiploc,
            arr,
            dep,
            platform,
            mileage_map[call_crs],
            divisions_at_this_call
        )
        locations_with_current_formation.append(location)
        # Check if we have reached a call at which the formation changes
        if current_formation is not None and len(allocations) != 0 and call_crs == current_formation.until:
            formations.append(
                (current_formation, locations_with_current_formation))
            current_formation = allocations.pop(0)
            locations_with_current_formation = [location]
    # Append the current formation as we never reached the end
    formations.append((current_formation, locations_with_current_formation))
    return (formations, division_services)


def make_service(uid: str, service_date: date, credentials: Credentials, network: Network) -> Service:
    service_json = request_service(uid, service_date, credentials)

    def map_short_locations(short_locs: list[Dict[str, Any]]) -> list[ShortLocation]:
        return list(map(
            lambda loc:
                ShortLocation(
                    loc["description"],
                    get_station_crs_from_name(network, loc["description"]),
                    loc["tiploc"]
                ), short_locs))

    service_uid = service_json["serviceUid"]
    url = get_service_url(service_uid, service_date)
    headcode = service_json["trainIdentity"]
    origins = map_short_locations(service_json["origin"])
    destinations = map_short_locations(service_json["destination"])
    power = service_json["powerType"]
    toc_code = service_json["atocCode"]
    toc = get_toc(origins, destinations, service_json["atocName"], network)
    (calls, other_services) = get_calls(
        service_date, service_json, credentials, network)

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

    return service


def calls_at(service: Service, station: Station) -> bool:
    for (_, locs) in service.calls:
        for loc in locs:
            if loc.crs == station.crs:
                return True
            for associated_service in loc.split:
                if calls_at(associated_service, station):
                    return True
    return False


def search_for_services(origin: Station, destination: Station) -> list[Service]:
    services_at_origin = origin.services
    services_to_destination: list[Service] = []
    for service in services_at_origin:
        if calls_at(service, origin):
            services_to_destination.append(service)
    return services_to_destination


def get_short_service_name(service: Service) -> str:
    origin_string = get_multiple_location_string(service.origins)
    destination_string = get_multiple_location_string(service.destinations)

    return f"{service.headcode} {service.origins[0].time} {origin_string} to {destination_string}"

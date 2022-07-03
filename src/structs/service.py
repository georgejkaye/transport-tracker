from dataclasses import dataclass
from datetime import date
from typing import Any, Dict
from api import Credentials, request_service
from location import Location, ShortLocation
from network import get_station_crs_from_name, lnwr_dests
from record import make_planact_entry
from structures import PlanActTime
from times import make_planact


class Allocation:
    stock: list[int]


def get_service_url(uid: str, service_date: date) -> str:
    date_string = service_date.strftime("%Y-%m-%d")
    return f"https://www.realtimetrains.co.uk/service/gb-nr:{uid}/{date_string}/detailed"


@dataclass
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


def get_toc(toc: str) -> str:
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


def get_calls(date: date, calls: list[Dict[str, Any]]) -> tuple[list[tuple[Allocation, list[Location]]], list[tuple[str, str]]]:
    splits = []
    for call in calls:
        arr = make_planact(date, call.get("gbttBookedArrival"),
                           call.get("realtimeArrival"))
        dep = make_planact(date, call.get("gbttBookedDeparture"),
                           call.get("realtimeDeparture"))
        location = Location(
            call.get("description"),
            call.get("crs"),
            call.get("tiploc"),
            arr,
            dep,
            call.get("platform")
        )
        # Get mileage

        # Get unit allocations

        # Check for if the service divides
        associations = call.get("associations")
        if associations is not None:
            for assoc in associations:
                assoc_type = assoc.get("type")
                if assoc_type == "divide":
                    splits.append((assoc.get("associatedUid"),
                                  assoc.get("associatedRundate")))


def make_services(uid: str, service_date: date, credentials: Credentials) -> list[Service]:
    service_json = request_service(uid, service_date, credentials)

    def map_short_locations(short_locs: list[Dict[str, Any]]) -> list[ShortLocation]:
        return list(map(
            lambda loc:
                ShortLocation(
                    loc["description"],
                    get_station_crs_from_name(loc["description"]),
                    loc["tiploc"]
                )
        ))

    service_uid = service_json.get("serviceUid")
    headcode = service_json.get("trainIdentity")
    origins = map_short_locations(service_json.get("origins"))
    destinations = map_short_locations(service_json.get("destinations"))
    power = service_json.get("power")
    toc_code = service_json.get("atocCode")
    toc = get_toc(service_json.get("atocName"))
    calls = get_calls(service_json.get("locations"))

    url = get_service_url(service_uid, service_date)

    let service = Service(
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

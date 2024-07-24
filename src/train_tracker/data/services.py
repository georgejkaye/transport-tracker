from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from bs4 import BeautifulSoup

from train_tracker.data.core import get_soup, make_get_request
from train_tracker.data.credentials import get_api_credentials
from train_tracker.data.database import connect, disconnect
from train_tracker.data.network import miles_and_chains_to_miles
from train_tracker.data.stations import (
    ShortTrainStation,
    TrainServiceAtStation,
    TrainStation,
    compare_crs,
    response_to_short_train_station,
)
from train_tracker.times import get_datetime_route

from psycopg2._psycopg import cursor


@dataclass
class Call:
    station: ShortTrainStation
    plan_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_arr: Optional[datetime]
    act_dep: Optional[datetime]
    divide: list["TrainService"]
    join: list["TrainService"]


@dataclass
class TrainService:
    id: str
    headcode: str
    run_date: datetime
    origins: list[ShortTrainStation]
    destinations: list[ShortTrainStation]
    operator_name: str
    operator_id: str
    brand_id: str
    power: Optional[str]
    calls: list[Call]


service_endpoint = "https://api.rtt.io/api/v1/json/service"


def get_calls(calls: list[Call], origin: str, dest: str) -> Optional[list[Call]]:
    call_chain = []
    boarded = False
    for call in calls:
        if boarded and compare_crs(call.station.crs, dest):
            call_chain.append(call)
            return calls
        # Since divisions include the current call as their initial call,
        # we iterate into them first to see if there is a path from the origin
        # (if the origin has not been encountered) or the current station (if
        # the origin has been encountered) to the destination.
        # If there is, we concat this list to the existing list and return it.
        divide_start = origin
        if boarded:
            divide_start = call.station.crs
        for divide in call.divide:
            subcalls = get_calls(divide.calls, divide_start, dest)
            if subcalls is not None:
                call_chain.extend(subcalls)
                return call_chain
        # Otherwise we keep checking in this list
        if boarded:
            call_chain.append(call)
            if compare_crs(call.station.crs, dest):
                return call_chain
        elif compare_crs(call.station.crs, origin):
            boarded = True
    return None


def string_of_calls(calls: list[Call], branch: bool = True, level: int = 0) -> str:
    string = ""
    for i, call in enumerate(calls):
        stop_symbol = "| " * level
        if i == 0 or i == len(calls) - 1:
            stop_symbol = f"{stop_symbol}* "
        else:
            stop_symbol = f"{stop_symbol}| "
        call_string = f"{stop_symbol}{call.station.name} [{call.station.crs}]"
        if string == "":
            string = call_string
        else:
            string = f"{string}\n{call_string}"
        assocs = False
        if branch:
            for join in call.join:
                join_string = string_of_calls(join.calls, branch, level + 1)
                string = f"{string}\n\n{join_string}\n{"|" * (level + 1)}/"
                assocs = True
            for divide in call.divide:
                divide_string = string_of_calls(divide.calls, branch, level + 1)
                string = f"{string}\n{"|" * (level + 1)}\\\n{divide_string}\n{"|" * (level + 1)}"
                assocs = True
        if assocs:
            string = f"{string}\n{call_string}"
    return string


def response_to_time(
    run_date: datetime, time_field: str, data: dict
) -> Optional[datetime]:
    time_string = data.get(time_field)
    if time_string is None:
        return None
    next_day = data.get(f"{time_field}NextDay")
    if next_day is not None and next_day:
        days_offset = 1
    else:
        days_offset = 0
    new_time = run_date + timedelta(
        days=days_offset, hours=int(time_string[0:2]), minutes=int(time_string[2:4])
    )
    return new_time


def response_to_call(
    cur: cursor,
    run_date: datetime,
    data: dict,
    current_uid: str,
    parent_uid: Optional[str] = None,
) -> Call:
    station = ShortTrainStation(data["description"], data["crs"])
    plan_arr = response_to_time(run_date, "gbttBookedArrival", data)
    plan_dep = response_to_time(run_date, "gbttBookedDeparture", data)
    act_arr = response_to_time(run_date, "realtimeArrival", data)
    act_dep = response_to_time(run_date, "realtimeDeparture", data)
    divides = []
    joins = []
    assocs = data.get("associations")
    if assocs is not None:
        for assoc in assocs:
            assoc_uid = assoc["associatedUid"]
            if (
                parent_uid is None
                or not parent_uid == assoc_uid
                and (assoc["type"] == "divide" or assoc["type"] == "join")
            ):
                assoc_date = datetime.strptime(assoc["associatedRunDate"], "%Y-%m-%d")
                associated_service = get_service_from_id(
                    cur, assoc_uid, assoc_date, current_uid
                )
                if assoc["type"] == "divide":
                    divides.append(associated_service)
                elif assoc["type"] == "join":
                    joins.append(associated_service)
    return Call(station, plan_arr, plan_dep, act_arr, act_dep, divides, joins)


def get_service_from_id(
    cur: cursor, service_id: str, run_date: datetime, parent: Optional[str] = None
) -> Optional[TrainService]:
    endpoint = f"{service_endpoint}/{service_id}/{get_datetime_route(run_date, False)}"
    rtt_credentials = get_api_credentials("RTT")
    response = make_get_request(endpoint, rtt_credentials)
    data = response.json()
    if data["isPassenger"]:
        headcode = data["trainIdentity"]
        power = data.get("powerType")
        origins = [
            response_to_short_train_station(cur, origin) for origin in data["origin"]
        ]
        destinations = [
            response_to_short_train_station(cur, destination)
            for destination in data["destination"]
        ]
        operator_name = data["atocName"]
        operator_id = data["atocCode"]
        calls: list[Call] = []
        for loc in data["locations"]:
            if loc.get("crs") is not None:
                call = response_to_call(cur, run_date, loc, service_id, parent)
                calls.append(call)
        brand_id = ""
        return TrainService(
            service_id,
            headcode,
            run_date,
            origins,
            destinations,
            operator_name,
            operator_id,
            brand_id,
            power,
            calls,
        )
    return None


def filter_services_by_time(
    earliest: datetime, latest: datetime, services: list[TrainServiceAtStation]
) -> list[TrainServiceAtStation]:
    filtered_services = []
    for service in services:
        if (
            service.plan_dep
            and service.plan_dep >= earliest
            and service.plan_dep <= latest
        ) or (
            service.act_dep
            and service.act_dep >= earliest
            and service.act_dep <= latest
        ):
            filtered_services.append(service)
    return filtered_services


def stops_at_station(
    service: TrainService, origin_crs: str, destination_crs: str
) -> bool:
    return get_calls(service.calls, origin_crs, destination_crs) is not None


def filter_services_by_time_and_stop(
    cur: cursor,
    earliest: datetime,
    latest: datetime,
    origin: TrainStation,
    destination: TrainStation,
    services: list[TrainServiceAtStation],
) -> list[TrainServiceAtStation]:
    time_filtered = filter_services_by_time(earliest, latest, services)
    stop_filtered: list[TrainServiceAtStation] = []
    for service in time_filtered:
        full_service = get_service_from_id(cur, service.id, service.run_date)
        if full_service and stops_at_station(full_service, origin.crs, destination.crs):
            stop_filtered.append(service)
    return stop_filtered


def get_service_page_url(service_date: datetime, id: str) -> str:
    date_string = service_date.strftime("%Y-%m-%d")
    return f"https://www.realtimetrains.co.uk/service/gb-nr:{id}/{date_string}/detailed"


def get_service_page(date: datetime, id: str) -> Optional[BeautifulSoup]:
    url = get_service_page_url(date, id)
    return get_soup(url)


def get_location_div_from_service_page(
    service_soup: BeautifulSoup, crs: str
) -> BeautifulSoup:
    calls = service_soup.find_all(class_="call")
    for call in calls:
        if crs.upper() in call.get_text():
            return call
    print("Could not get location div")
    exit(1)


def get_miles_and_chains_from_call_div(
    call_div_soup: BeautifulSoup,
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


def get_mileage_for_service_call(service: TrainService, crs: str) -> Optional[Decimal]:
    service_soup = get_service_page(service.run_date, service.id)
    if service_soup is None:
        return None
    call_div = get_location_div_from_service_page(service_soup, crs)
    if call_div is None:
        return None
    return get_miles_and_chains_from_call_div(call_div)


if __name__ == "__main__":
    (conn, cur) = connect()
    service = get_service_from_id(cur, "G38662", datetime(2024, 7, 24))
    if service is not None:
        print(string_of_calls(service.calls))
    disconnect(conn, cur)

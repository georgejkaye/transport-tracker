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


@dataclass
class CallTree:
    node: Call
    nexts: list["CallTree"]


def string_of_call_tree(call_tree: CallTree, level=0):
    string = (
        f"{' |' * level} | {call_tree.node.station.name} ({call_tree.node.station.crs})"
    )
    for i, next in enumerate(call_tree.nexts):
        string = f"{string}\n{string_of_call_tree(next, level + len(call_tree.nexts) - i - 1)}"
    return string


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
    call_tree: CallTree


service_endpoint = "https://api.rtt.io/api/v1/json/service"


def get_calls(stop_tree: CallTree, origin, dest, boarded=False) -> Optional[list[Call]]:
    node = stop_tree.node
    if boarded:
        if node.station.crs == dest:
            return [node]
        else:
            new_boarded = True
    elif node.station.crs == origin:
        new_boarded = True
    else:
        new_boarded = False
    for next in stop_tree.nexts:
        next_chain = get_calls(next, origin, dest, new_boarded)
        if new_boarded and next_chain is not None:
            next_chain.insert(0, node)
        return next_chain
    return None


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


def response_to_call(run_date: datetime, data: dict) -> Call:
    station = ShortTrainStation(data["crs"], data["description"])
    plan_arr = response_to_time(run_date, "gbttBookedArrival", data)
    plan_dep = response_to_time(run_date, "gbttBookedDeparture", data)
    act_arr = response_to_time(run_date, "realtimeArrival", data)
    act_dep = response_to_time(run_date, "realtimeDeparture", data)
    return Call(station, plan_arr, plan_dep, act_arr, act_dep)


def get_call_tree(
    locations: list[dict],
    run_date: datetime,
    service_id: str,
    parent_id="",
):
    current_nexts = []
    for call in reversed(locations):
        if call.get("crs") is not None:
            current_location = response_to_call(run_date, call)
            assocs = call.get("associations")
            if assocs is not None:
                for assoc in assocs:
                    if (
                        assoc["type"] == "divide"
                        and not assoc["associatedUid"] == parent_id
                    ):
                        assoc_uid = assoc["associatedUid"]
                        assoc_date = datetime.strptime(
                            assoc["associatedRunDate"], "%Y-%m-%d"
                        )
                        assoc_date_url = get_datetime_route(assoc_date, False)
                        endpoint = f"{service_endpoint}/{assoc_uid}/{assoc_date_url}"
                        response = make_get_request(
                            endpoint, get_api_credentials("RTT")
                        )
                        service_json = response.json()
                        if service_json.get("locations") is not None:
                            head_node = get_call_tree(
                                service_json["locations"],
                                assoc_date,
                                assoc_uid,
                                service_id,
                            )
                            current_nexts.append(head_node)
            current_node = CallTree(current_location, current_nexts)
            current_nexts = [current_node]
    return current_node


def get_service_from_id(
    cur: cursor, service_id: str, run_date: datetime
) -> Optional[TrainService]:
    endpoint = f"{service_endpoint}/{service_id}/{get_datetime_route(run_date, False)}"
    rtt_credentials = get_api_credentials("RTT")
    response = make_get_request(endpoint, rtt_credentials)
    data = response.json()
    headcode = data["trainIdentity"]
    power = data["powerType"]
    origins = [
        response_to_short_train_station(cur, origin) for origin in data["origin"]
    ]
    destinations = [
        response_to_short_train_station(cur, destination)
        for destination in data["destination"]
    ]
    operator_name = data["atocName"]
    operator_id = data["atocCode"]
    call_tree = get_call_tree(data["locations"], run_date, service_id)
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
        call_tree,
    )


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
    origin_crs: str, destination_crs: str, call_tree: CallTree, reached=False
):
    if not reached:
        if call_tree.node.station.crs == origin_crs:
            new_reached = True
        else:
            new_reached = False
    elif call_tree.node.station.crs == destination_crs:
        return True
    else:
        new_reached = True
    for next_call_tree in call_tree.nexts:
        if stops_at_station(origin_crs, destination_crs, next_call_tree, new_reached):
            return True
    return False


def filter_services_by_time_and_stop(
    cur: cursor,
    earliest: datetime,
    latest: datetime,
    origin: TrainStation,
    destination: TrainStation,
    services: list[TrainServiceAtStation],
) -> list[TrainServiceAtStation]:
    time_filtered = filter_services_by_time(earliest, latest, services)
    stop_filtered = []
    for service in time_filtered:
        full_service = get_service_from_id(cur, service.id, service.run_date)
        if full_service and stops_at_station(
            origin.crs, destination.crs, full_service.call_tree
        ):
            stop_filtered.append(full_service)
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
        if crs in call.get_text():
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
    service = get_service_from_id(cur, "L39994", datetime(2024, 7, 9))
    if service is not None:
        print(f"Root is {service.call_tree.node.station}")
        print(string_of_call_tree(service.call_tree))
    disconnect(conn, cur)

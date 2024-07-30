from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional

from bs4 import BeautifulSoup

from train_tracker.data.core import get_soup, make_get_request
from train_tracker.data.credentials import get_api_credentials
from train_tracker.data.database import (
    NoEscape,
    connect,
    datetime_or_none_to_raw_str,
    datetime_or_none_to_str,
    disconnect,
    insert,
)
from train_tracker.data.network import miles_and_chains_to_miles
from train_tracker.data.stations import (
    ShortTrainStation,
    TrainServiceAtStation,
    TrainStation,
    compare_crs,
    response_to_short_train_station,
    short_string_of_service_at_station,
    string_of_service_at_station,
)
from train_tracker.interactive import information
from train_tracker.times import get_datetime_route

from psycopg2._psycopg import cursor, connection


@dataclass
class Call:
    station: ShortTrainStation
    platform: str | None
    plan_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_arr: Optional[datetime]
    act_dep: Optional[datetime]
    divide: list["AssociatedService"]
    join: list["AssociatedService"]


AssociatedType = Enum(
    "AssociatedType", ["JOINS_TO", "JOINS_WITH", "DIVIDES_TO", "DIVIDES_FROM"]
)


def string_of_associated_type(at: AssociatedType) -> str:
    match at:
        case AssociatedType.JOINS_TO:
            return "JOINS_TO"
        case AssociatedType.JOINS_WITH:
            return "JOINS_WITH"
        case AssociatedType.DIVIDES_TO:
            return "DIVIDES_TO"
        case AssociatedType.DIVIDES_FROM:
            return "DIVIDES_FROM"


@dataclass
class AssociatedService:
    station: ShortTrainStation
    service: "TrainService"
    association: AssociatedType


@dataclass
class TrainService:
    id: str
    headcode: str
    run_date: datetime
    origins: list[ShortTrainStation]
    destinations: list[ShortTrainStation]
    operator_name: str
    operator_id: str
    brand_id: Optional[str]
    power: Optional[str]
    calls: list[Call]
    divides: list[AssociatedService]
    joins: list[AssociatedService]


service_endpoint = "https://api.rtt.io/api/v1/json/service"


@dataclass
class LegCall:
    service: TrainService
    station: ShortTrainStation
    platform: str | None
    plan_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_arr: Optional[datetime]
    act_dep: Optional[datetime]
    divide: Optional["AssociatedService"]


def get_calls(
    service: TrainService,
    calls: list[Call],
    origin: str,
    dest: str,
) -> Optional[list[LegCall]]:
    call_chain = []
    boarded = False
    for call in calls:
        current_call = LegCall(
            service,
            call.station,
            call.platform,
            call.plan_arr,
            call.plan_dep,
            call.act_arr,
            call.act_dep,
            None,
        )
        # Check if this call is the boarding call
        # If it is, then following the divide is forbidden
        # because the dividing service now has a completely
        # different departure time
        if not boarded and compare_crs(call.station.crs, origin):
            boarded = True
            call_chain.append(current_call)
        elif boarded and compare_crs(call.station.crs, dest):
            call_chain.append(current_call)
            return call_chain
        else:
            # Since divisions include the current call as their initial call,
            # we iterate into them first to see if there is a path from the origin
            # (if the origin has not been encountered) or the current station (if
            # the origin has been encountered) to the destination.
            # If there is, we concat this list to the existing list and return it.
            subservice_origin = origin
            if boarded:
                subservice_origin = call.station.crs
            for divide in call.divide:
                subcalls = get_calls(
                    divide.service, divide.service.calls, subservice_origin, dest
                )
                if subcalls is not None:
                    # If there is a divide that we are going to follow,
                    # we make a new call with the arrival of the parent
                    # and the departure of the child. This avoids duplicating
                    # the call from the parent and the child
                    current_call = LegCall(
                        divide.service,
                        call.station,
                        call.platform,
                        call.plan_arr,
                        subcalls[0].plan_dep,
                        call.act_arr,
                        subcalls[0].act_dep,
                        divide,
                    )
                    call_chain.append(current_call)
                    call_chain.extend(subcalls[1:])
                    return call_chain
            # Otherwise we keep checking in this list
            if boarded:
                call_chain.append(current_call)
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
                join_string = string_of_calls(join.service.calls, branch, level + 1)
                string = f"{string}\n\n{join_string}\n{"|" * (level + 1)}/"
                assocs = True
            for divide in call.divide:
                divide_string = string_of_calls(divide.service.calls, branch, level + 1)
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
    first: bool,
    last: bool,
    parent_uid: Optional[str] = None,
    parent_plan_arr: Optional[datetime] = None,
    parent_act_arr: Optional[datetime] = None,
) -> Call:
    station = ShortTrainStation(data["description"], data["crs"])
    plan_arr = response_to_time(run_date, "gbttBookedArrival", data)
    if plan_arr is None:
        plan_arr = parent_plan_arr
    plan_dep = response_to_time(run_date, "gbttBookedDeparture", data)
    act_arr = response_to_time(run_date, "realtimeArrival", data)
    if act_arr is None:
        act_arr = parent_act_arr
    act_dep = response_to_time(run_date, "realtimeDeparture", data)
    platform = data.get("platform")
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
                    cur, assoc_uid, assoc_date, current_uid, plan_arr, act_arr
                )
                if associated_service is not None:
                    if assoc["type"] == "divide":
                        if first:
                            assoc_type = AssociatedType.DIVIDES_FROM
                        else:
                            assoc_type = AssociatedType.DIVIDES_TO
                        divides.append(
                            AssociatedService(station, associated_service, assoc_type)
                        )
                    elif assoc["type"] == "join":
                        if last:
                            assoc_type = AssociatedType.JOINS_TO
                        else:
                            assoc_type = AssociatedType.JOINS_WITH
                        joins.append(
                            AssociatedService(station, associated_service, assoc_type)
                        )
    return Call(station, platform, plan_arr, plan_dep, act_arr, act_dep, divides, joins)


def get_service_from_id(
    cur: cursor,
    service_id: str,
    run_date: datetime,
    parent: Optional[str] = None,
    plan_arr: Optional[datetime] = None,
    act_arr: Optional[datetime] = None,
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
        divides: list[AssociatedService] = []
        joins: list[AssociatedService] = []
        for i, loc in enumerate(data["locations"]):
            if loc.get("crs") is not None:
                call = response_to_call(
                    cur,
                    run_date,
                    loc,
                    service_id,
                    i == 0,
                    i == len(data["locations"]) - 1,
                    parent,
                    plan_arr,
                    act_arr,
                )
                divides.extend(call.divide)
                joins.extend(call.join)
                calls.append(call)
        brand_id = None
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
            divides,
            joins,
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
    return get_calls(service, service.calls, origin_crs, destination_crs) is not None


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
    max_string_length = 0
    for i, service in enumerate(time_filtered):
        string = f"Checking service {i}/{len(time_filtered)}: {short_string_of_service_at_station(service)}"
        max_string_length = max(max_string_length, len(string))
        information(string.ljust(max_string_length), end="\r")
        full_service = get_service_from_id(cur, service.id, service.run_date)
        if full_service and stops_at_station(full_service, origin.crs, destination.crs):
            stop_filtered.append(service)
    information(" " * max_string_length, end="\r")
    return stop_filtered


def get_service_page_url(service_date: datetime, id: str) -> str:
    date_string = service_date.strftime("%Y-%m-%d")
    return f"https://www.realtimetrains.co.uk/service/gb-nr:{id}/{date_string}/detailed"


def get_service_page_url_from_service(service: TrainService) -> str:
    return get_service_page_url(service.run_date, service.id)


def get_service_pages(
    service: TrainService, calls: list[LegCall]
) -> Optional[list[BeautifulSoup]]:
    initial_url = get_service_page_url(service.run_date, service.id)
    initial_soup = get_soup(initial_url)
    if initial_soup is None:
        return None
    soups = [initial_soup]
    for call in calls:
        if call.divide is not None:
            call_url = get_service_page_url(
                call.divide.service.run_date, call.divide.service.id
            )
            call_soup = get_soup(call_url)
            if call_soup is None:
                return None
            soups.append(call_soup)
    return soups


def get_service_page(service: TrainService) -> Optional[BeautifulSoup]:
    url = get_service_page_url_from_service(service)
    soup = get_soup(url)
    return soup


def get_location_div_from_service_page(
    service_soup: BeautifulSoup, crs: str
) -> Optional[BeautifulSoup]:
    calls = service_soup.find_all(class_="call")
    for call in calls:
        if crs.upper() in call.get_text():
            return call
    return None


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


def get_distance_between_calls(service: TrainService, calls: list[LegCall]):
    current_soup = get_service_page(service)
    if current_soup is None:
        return None
    # We iterate through the calls, but we only care if we reach
    # the final destination or a point of division, as the call divs
    # contain cumulative distance
    base_mileage = Decimal(0)
    start_mileage = Decimal(0)
    for i, call in enumerate(calls):
        if i == 0 or i == len(calls) - 1 or call.divide:
            call_div = get_location_div_from_service_page(
                current_soup, call.station.crs
            )
            if call_div is None:
                return None
            call_mileage_opt = get_miles_and_chains_from_call_div(call_div)
            if call_mileage_opt is None:
                return None
            call_mileage = call_mileage_opt + base_mileage
            # If this is the first call, store the initial mileage
            if i == 0:
                start_mileage = call_mileage
            # If this is the final call, return the difference between this
            # and the start mileage
            if i == len(calls) - 1:
                return call_mileage - start_mileage
            # If this is a division, the next page will start mileage from
            # zero so we need to set the base mileage and repeat on the
            # new page
            if call.divide:
                base_mileage = call_mileage
                current_soup = get_service_page(call.divide.service)
                if current_soup is None:
                    return None


def get_distance_between_stations(
    service: TrainService, origin: str, destination: str
) -> Optional[Decimal]:
    calls = get_calls(service, service.calls, origin, destination)
    if calls is None:
        return None
    return get_distance_between_calls(service, calls)


def insert_services(conn: connection, cur: cursor, services: list[TrainService]):
    service_fields = [
        "service_id",
        "run_date",
        "headcode",
        "operator_id",
        "brand_id",
        "power",
    ]
    endpoint_fields = ["service_id", "run_date", "station_crs", "origin"]
    call_fields = [
        "service_id",
        "run_date",
        "station_crs",
        "platform",
        "plan_arr",
        "plan_dep",
        "act_arr",
        "act_dep",
    ]
    assoc_fields = [
        "call_id",
        "associated_id",
        "associated_run_date",
        "associated_type",
    ]
    service_values = []
    endpoint_values = []
    call_values = []
    assoc_values = []
    for service in services:
        service_values.append(
            [
                str(service.id),
                service.run_date.isoformat(),
                service.headcode,
                service.operator_id,
                service.brand_id,
                service.power,
            ]
        )
        for origin in service.origins:
            endpoint_values.append(
                [str(service.id), service.run_date.isoformat(), origin.crs, str(True)]
            )
        for destination in service.destinations:
            endpoint_values.append(
                [
                    str(service.id),
                    service.run_date.isoformat(),
                    destination.crs,
                    str(False),
                ]
            )
        for call in service.calls:
            call_values.append(
                [
                    service.id,
                    service.run_date.isoformat(),
                    call.station.crs,
                    call.platform,
                    datetime_or_none_to_str(call.plan_arr),
                    datetime_or_none_to_str(call.plan_dep),
                    datetime_or_none_to_str(call.act_arr),
                    datetime_or_none_to_str(call.act_dep),
                ]
            )
            select_call_id_statement = f"""(
                SELECT call_id FROM Call
                WHERE service_id = '{service.id}'
                AND run_date = '{service.run_date.isoformat()}'
                AND station_crs = '{call.station.crs}'
                AND plan_arr = {datetime_or_none_to_raw_str(call.plan_arr)}
                AND plan_dep = {datetime_or_none_to_raw_str(call.plan_dep)}
            )"""
            for divide in call.divide + call.join:
                assoc_values.append(
                    [
                        NoEscape(select_call_id_statement),
                        divide.service.id,
                        divide.service.run_date.isoformat(),
                        string_of_associated_type(divide.association),
                    ]
                )
    insert(
        cur,
        "Service",
        service_fields,
        service_values,
        additional_query="ON CONFLICT DO NOTHING",
    )
    insert(
        cur,
        "ServiceEndpoint",
        endpoint_fields,
        endpoint_values,
        additional_query="ON CONFLICT DO NOTHING",
    )
    insert(
        cur, "Call", call_fields, call_values, additional_query="ON CONFLICT DO NOTHING"
    )
    insert(
        cur,
        "AssociatedService",
        assoc_fields,
        assoc_values,
        additional_query="ON CONFLICT DO NOTHING",
    )
    conn.commit()


if __name__ == "__main__":
    (conn, cur) = connect()
    service = get_service_from_id(cur, "G38662", datetime(2024, 7, 24))
    if service is not None:
        print(string_of_calls(service.calls))
    disconnect(conn, cur)

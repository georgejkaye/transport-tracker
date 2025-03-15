import copy

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional
from bs4 import BeautifulSoup
from psycopg import Connection, Cursor

from api.utils.request import get_soup, make_get_request
from api.utils.credentials import get_api_credentials
from api.data.mileage import miles_and_chains_to_miles
from api.data.stations import (
    ShortTrainStation,
    TrainServiceAtStation,
    TrainStation,
    compare_crs,
    response_to_short_train_station,
    short_string_of_service_at_station,
)
from api.data.toc import BrandData, OperatorData
from api.utils.interactive import information
from api.utils.times import get_datetime_route, make_timezone_aware


@dataclass
class Call:
    service_id: str
    run_date: datetime
    station: ShortTrainStation
    platform: Optional[str]
    plan_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_arr: Optional[datetime]
    act_dep: Optional[datetime]
    divide: list["AssociatedService"]
    join: list["AssociatedService"]
    mileage: Optional[Decimal]


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


def string_to_associated_type(string: str) -> Optional[AssociatedType]:
    if string == "JOINS_TO":
        return AssociatedType.JOINS_TO
    if string == "JOINS_WITH":
        return AssociatedType.JOINS_WITH
    if string == "DIVIDES_TO":
        return AssociatedType.DIVIDES_TO
    if string == "DIVIDES_FROM":
        return AssociatedType.DIVIDES_FROM
    return None


@dataclass
class AssociatedService:
    station: ShortTrainStation
    service: "TrainServiceRaw"
    association: AssociatedType


@dataclass
class ShortAssociatedService:
    service_id: str
    service_run_date: datetime
    association: str


@dataclass
class ShortCall:
    station: ShortTrainStation
    platform: Optional[str]
    plan_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_arr: Optional[datetime]
    act_dep: Optional[datetime]
    assocs: list[ShortAssociatedService]
    mileage: Optional[Decimal]


@dataclass
class TrainServiceRaw:
    id: str
    headcode: str
    run_date: datetime
    origins: list[ShortTrainStation]
    destinations: list[ShortTrainStation]
    operator_name: str
    operator_code: str
    brand_code: Optional[str]
    power: Optional[str]
    calls: list[Call]
    divides: list[AssociatedService]
    joins: list[AssociatedService]


@dataclass
class ShortTrainService:
    service_id: str
    headcode: str
    run_date: datetime
    service_start: datetime
    origins: list[ShortTrainStation]
    destinations: list[ShortTrainStation]
    operator: OperatorData
    brand: Optional[BrandData]
    power: Optional[str]
    calls: list[ShortCall]
    assocs: list[ShortAssociatedService]


service_endpoint = "https://api.rtt.io/api/v1/json/service"


@dataclass
class LegCall:
    station: ShortTrainStation
    arr_call: Optional[Call]
    dep_call: Optional[Call]
    mileage: Optional[Decimal]
    change_type: Optional[AssociatedType]


def get_calls_between_stations(
    service: TrainServiceRaw,
    calls: list[Call],
    origin: str,
    dest: str,
    base_mileage: Decimal = Decimal(0),
) -> Optional[tuple[list[LegCall], deque[list[LegCall]]]]:
    call_chain: list[LegCall] = []
    service_chains = deque()
    boarded = False
    dep_call = None
    for i, call in enumerate(calls):
        # Get the arrival call
        # If this is the boarding point there is no arrival
        if not boarded:
            arr_call = None
            if compare_crs(call.station.crs, origin):
                boarded = True
                if call.mileage is None:
                    base_mileage = Decimal(0)
                else:
                    base_mileage = base_mileage - call.mileage
                call_mileage = Decimal(0)
            else:
                call_mileage = None

        else:
            arr_call = call
            if call.mileage is None:
                call_mileage = None
            else:
                call_mileage = base_mileage + call.mileage
        # Get the departure call
        # This might belong to a different service if there is a join or divide
        # To check this we recurse into any associations to see if the
        # destination is there, searching for the entire leg if we haven't
        # boarded or the rest of the leg if we have
        if boarded:
            subservice_origin = call.station.crs
        else:
            subservice_origin = origin
        # If we branch off to a divided service, the mileage resets to 0, so we
        # need to set the base mileage to the current call mileage
        if call_mileage is None:
            divide_base_mileage = Decimal(0)
        else:
            divide_base_mileage = call_mileage
        # If we do change services, we keep track of the rest of the calls
        remaining_calls = []
        assoc_type = None
        # If we have reached our destination then we don't care about departure
        # calls
        if compare_crs(call.station.crs, dest):
            dep_call = None
        else:
            # First we check the divides
            for divide in call.divide:
                subresult = get_calls_between_stations(
                    divide.service,
                    divide.service.calls,
                    subservice_origin,
                    dest,
                    divide_base_mileage,
                )
                if subresult is not None:
                    subservice_calls, subservice_chains = subresult
                    dep_call = subservice_calls[0].dep_call
                    remaining_calls = subservice_calls[1:]
                    assoc_type = AssociatedType.DIVIDES_FROM
                    service_chains.extendleft(subservice_chains)
                    # No need to check the rest of the divides
                    break
            # If we haven't divided, perhaps we're about to join
            # We can only join if we're at the end of the service
            if assoc_type is None and i == len(calls) - 1:
                # This should always be the case
                if len(call.join) == 1:
                    join = call.join[0]
                    # The mileage in the subservice will be relative to its own origin
                    # We want the mileage to be relative to our
                    # need to set the base mileage to the current call mileage
                    if call_mileage is None:
                        join_base_mileage = Decimal(0)
                    else:
                        join_base_mileage = call_mileage
                    subresult = get_calls_between_stations(
                        join.service,
                        join.service.calls,
                        subservice_origin,
                        dest,
                        join_base_mileage,
                    )
                    if subresult is not None:
                        subservice_calls, service_chains = subresult
                        dep_call = subservice_calls[0].dep_call
                        remaining_calls = subservice_calls[1:]
                        assoc_type = AssociatedType.JOINS_TO
                        service_chains.extendleft(service_chains)
            if assoc_type is None and boarded:
                dep_call = call
        if boarded:
            leg_call = LegCall(
                call.station, arr_call, dep_call, call_mileage, assoc_type
            )
            call_chain.append(leg_call)
            if len(remaining_calls) > 0:
                service_chains.extendleft([copy.deepcopy(call_chain)])
                call_chain.extend(remaining_calls)
                return (call_chain, service_chains)
            if dep_call is None:
                service_chains.extendleft([call_chain])
                return (call_chain, service_chains)
    return None


def string_of_calls(
    calls: list[Call], branch: bool = True, level: int = 0
) -> str:
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
                join_string = string_of_calls(
                    join.service.calls, branch, level + 1
                )
                string = f"{string}\n\n{join_string}\n{"|" * (level + 1)}/"
                assocs = True
            for divide in call.divide:
                divide_string = string_of_calls(
                    divide.service.calls, branch, level + 1
                )
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
        days=days_offset,
        hours=int(time_string[0:2]),
        minutes=int(time_string[2:4]),
    )
    return make_timezone_aware(new_time)


def response_to_call(
    cur: Cursor,
    service_id: str,
    service_soup: Optional[BeautifulSoup],
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
                assoc_date = datetime.strptime(
                    assoc["associatedRunDate"], "%Y-%m-%d"
                )
                if service_soup is None:
                    subsoup = False
                else:
                    subsoup = True
                associated_service = get_service_from_id(
                    cur,
                    assoc_uid,
                    assoc_date,
                    current_uid,
                    plan_arr,
                    act_arr,
                    soup=subsoup,
                )
                if associated_service is not None:
                    if assoc["type"] == "divide":
                        if first:
                            assoc_type = AssociatedType.DIVIDES_FROM
                        else:
                            assoc_type = AssociatedType.DIVIDES_TO
                        divides.append(
                            AssociatedService(
                                station, associated_service, assoc_type
                            )
                        )
                    elif assoc["type"] == "join":
                        if last:
                            assoc_type = AssociatedType.JOINS_TO
                        else:
                            assoc_type = AssociatedType.JOINS_WITH
                        joins.append(
                            AssociatedService(
                                station, associated_service, assoc_type
                            )
                        )
    if service_soup is None:
        mileage = None
    else:
        call_div = get_location_div_from_service_page(service_soup, station.crs)
        if call_div is None:
            mileage = None
        else:
            mileage = get_miles_and_chains_from_call_div(call_div)
    return Call(
        service_id,
        run_date,
        station,
        platform,
        plan_arr,
        plan_dep,
        act_arr,
        act_dep,
        divides,
        joins,
        mileage,
    )


def get_service_from_id(
    cur: Cursor,
    service_id: str,
    run_date: datetime,
    parent: Optional[str] = None,
    plan_arr: Optional[datetime] = None,
    act_arr: Optional[datetime] = None,
    soup: bool = False,
) -> Optional[TrainServiceRaw]:
    endpoint = (
        f"{service_endpoint}/{service_id}/{get_datetime_route(run_date, False)}"
    )
    rtt_credentials = get_api_credentials("RTT")
    response = make_get_request(endpoint, rtt_credentials)
    data = response.json()
    if data.get("isPassenger") and data.get("serviceType") == "train":
        headcode = data["trainIdentity"]
        power = data.get("powerType")
        origins = [
            response_to_short_train_station(cur, origin)
            for origin in data["origin"]
        ]
        destinations = [
            response_to_short_train_station(cur, destination)
            for destination in data["destination"]
        ]
        operator_name = data["atocName"]
        operator_code = data["atocCode"]
        calls: list[Call] = []
        divides: list[AssociatedService] = []
        joins: list[AssociatedService] = []
        if soup:
            service_soup = get_service_page(service_id, run_date)
        else:
            service_soup = None
        for i, loc in enumerate(data["locations"]):
            if loc.get("crs") is not None:
                call = response_to_call(
                    cur,
                    service_id,
                    service_soup,
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
        brand_code = None
        return TrainServiceRaw(
            service_id,
            headcode,
            run_date,
            origins,
            destinations,
            operator_name,
            operator_code,
            brand_code,
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
    service: TrainServiceRaw, origin_crs: str, destination_crs: str
) -> bool:
    return (
        get_calls_between_stations(
            service, service.calls, origin_crs, destination_crs
        )
        is not None
    )


def filter_services_by_time_and_stop(
    cur: Cursor,
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
        full_service = get_service_from_id(
            cur, service.id, service.run_date, soup=False
        )
        if full_service and stops_at_station(
            full_service, origin.crs, destination.crs
        ):
            stop_filtered.append(service)
    information(" " * max_string_length, end="\r")
    return stop_filtered


def get_service_page_url(id: str, service_date: datetime) -> str:
    date_string = service_date.strftime("%Y-%m-%d")
    return f"https://www.realtimetrains.co.uk/service/gb-nr:{id}/{date_string}/detailed"


def get_service_page_url_from_service(service: TrainServiceRaw) -> str:
    return get_service_page_url(service.id, service.run_date)


def get_service_page(
    service_id: str, run_date: datetime
) -> Optional[BeautifulSoup]:
    url = get_service_page_url(service_id, run_date)
    soup = get_soup(url)
    return soup


def get_service_page_from_service(
    service: TrainServiceRaw,
) -> Optional[BeautifulSoup]:
    get_service_page(service.id, service.run_date)


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


def insert_services(
    conn: Connection, cur: Cursor, services: list[TrainServiceRaw]
):
    service_values = []
    endpoint_values = []
    call_values = []
    assoc_values = []
    for service in services:
        service_values.append(
            (
                service.id,
                service.run_date.isoformat(),
                service.headcode,
                service.operator_code,
                service.brand_code,
                service.power,
            )
        )
        for origin in service.origins:
            endpoint_values.append(
                (
                    service.id,
                    service.run_date,
                    origin.crs,
                    True,
                )
            )
        for destination in service.destinations:
            endpoint_values.append(
                (
                    service.id,
                    service.run_date,
                    destination.crs,
                    False,
                )
            )
        for call in service.calls:
            call_values.append(
                (
                    service.id,
                    service.run_date,
                    call.station.crs,
                    call.platform,
                    call.plan_arr,
                    call.plan_dep,
                    call.act_arr,
                    call.act_dep,
                    call.mileage,
                )
            )
            for divide in call.divide + call.join:
                assoc_values.append(
                    (
                        service.id,
                        service.run_date,
                        call.station.crs,
                        call.plan_arr,
                        call.plan_dep,
                        call.act_arr,
                        call.act_dep,
                        divide.service.id,
                        divide.service.run_date.isoformat(),
                        string_of_associated_type(divide.association),
                    )
                )
    cur.execute(
        """
        SELECT * FROM InsertServices(
            %s::service_data[],
            %s::endpoint_data[],
            %s::call_data[],
            %s::assoc_data[]
        )
        """,
        [service_values, endpoint_values, call_values, assoc_values],
    )
    conn.commit()

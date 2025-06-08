from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from api.utils.database import register_type
from bs4 import BeautifulSoup, Tag
from psycopg import Connection

from api.utils.request import get_soup, make_get_request
from api.utils.credentials import get_api_credentials
from api.data.train.mileage import miles_and_chains_to_miles
from api.data.train.stations import (
    TrainLegCallStationInData,
    register_short_train_station_types,
)
from api.data.train.toc import (
    BrandData,
    OperatorData,
    register_brand_data_types,
)
from api.utils.times import (
    change_timezone,
    get_datetime_route,
    make_timezone_aware,
)

AssociatedType = Enum(
    "AssociatedType",
    ["THIS_JOINS", "OTHER_JOINS", "THIS_DIVIDES", "OTHER_DIVIDES"],
)


@dataclass
class TrainServiceCallAssociatedServiceInData:
    service_unique_identifier: str
    service_run_date: datetime
    association: AssociatedType


@dataclass
class TrainServiceCallInData:
    station_crs: str
    station_name: str
    platform: Optional[str]
    plan_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_arr: Optional[datetime]
    act_dep: Optional[datetime]
    assocs: list[TrainServiceCallAssociatedServiceInData]
    mileage: Optional[Decimal]


def string_of_associated_type(at: AssociatedType) -> str:
    match at:
        case AssociatedType.THIS_JOINS:
            return "THIS_JOINS"
        case AssociatedType.OTHER_JOINS:
            return "OTHER_JOINS"
        case AssociatedType.THIS_DIVIDES:
            return "THIS_DIVIDES"
        case AssociatedType.OTHER_DIVIDES:
            return "OTHER_DIVIDES"


def string_to_associated_type(string: str) -> Optional[AssociatedType]:
    if string == "JOINS_TO":
        return AssociatedType.THIS_JOINS
    if string == "JOINS_WITH":
        return AssociatedType.OTHER_JOINS
    if string == "DIVIDES_TO":
        return AssociatedType.THIS_DIVIDES
    if string == "DIVIDES_FROM":
        return AssociatedType.OTHER_DIVIDES
    return None


@dataclass
class ShortAssociatedService:
    service_id: str
    service_run_date: datetime
    association: str


def register_assoc_data(
    assoc_service_id: str, assoc_service_run_date: datetime, assoc_type: str
):
    return ShortAssociatedService(
        assoc_service_id, assoc_service_run_date, assoc_type
    )


def register_short_associated_service_types(conn: Connection):
    register_type(conn, "TrainAssociatedServiceOutData", register_assoc_data)


@dataclass
class ShortCall:
    station: TrainLegCallStationInData
    platform: Optional[str]
    plan_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_arr: Optional[datetime]
    act_dep: Optional[datetime]
    assocs: list[ShortAssociatedService]
    mileage: Optional[Decimal]


def register_call_data(
    station: TrainLegCallStationInData,
    platform: str,
    plan_arr: datetime,
    act_arr: datetime,
    plan_dep: datetime,
    act_dep: datetime,
    assocs: list[ShortAssociatedService],
    mileage: Decimal,
):
    return ShortCall(
        station,
        platform,
        change_timezone(plan_arr),
        change_timezone(act_arr),
        change_timezone(plan_dep),
        change_timezone(act_dep),
        assocs,
        mileage,
    )


def register_short_call_types(conn: Connection):
    register_short_train_station_types(conn)
    register_short_associated_service_types(conn)
    register_type(conn, "TrainCallOutData", register_call_data)


@dataclass
class TrainServiceInData:
    unique_identifier: str
    run_date: datetime
    headcode: str
    origin_names: list[str]
    destination_names: list[str]
    operator_code: str
    brand_code: Optional[str]
    power: Optional[str]
    calls: list[TrainServiceCallInData]


@dataclass
class ShortTrainService:
    service_id: str
    headcode: str
    run_date: datetime
    service_start: datetime
    origins: list[TrainLegCallStationInData]
    destinations: list[TrainLegCallStationInData]
    operator: OperatorData
    brand: Optional[BrandData]
    power: Optional[str]
    calls: list[ShortCall]
    assocs: list[ShortAssociatedService]


def register_service_data(
    service_id: str,
    service_run_date: datetime,
    service_headcode: str,
    service_start: datetime,
    service_origins: list[TrainLegCallStationInData],
    service_destinations: list[TrainLegCallStationInData],
    service_operator: OperatorData,
    service_brand: Optional[BrandData],
    service_calls: list[ShortCall],
    service_assocs: list[ShortAssociatedService],
):
    return ShortTrainService(
        service_id,
        service_headcode,
        service_run_date,
        service_start,
        service_origins,
        service_destinations,
        service_operator,
        service_brand,
        None,
        service_calls,
        service_assocs,
    )


def register_short_train_service_types(conn: Connection):
    register_short_train_station_types(conn)
    register_brand_data_types(conn)
    register_short_call_types(conn)
    register_short_associated_service_types(conn)
    register_type(conn, "TrainServiceOutData", register_service_data)


service_endpoint = "https://api.rtt.io/api/v1/json/service"


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


def get_call_assoc(
    assoc: dict, first: bool, last: bool
) -> Optional[TrainServiceCallAssociatedServiceInData]:
    assoc_uid = assoc["associatedUid"]
    assoc_date = datetime.strptime(assoc["associatedRunDate"], "%Y-%m-%d")
    if assoc["type"] == "divide":
        if first:
            assoc_type = AssociatedType.THIS_DIVIDES
        else:
            assoc_type = AssociatedType.OTHER_DIVIDES
    elif assoc["type"] == "join":
        if last:
            assoc_type = AssociatedType.THIS_JOINS
        else:
            assoc_type = AssociatedType.OTHER_DIVIDES
    else:
        return None
    return TrainServiceCallAssociatedServiceInData(
        assoc_uid, assoc_date, assoc_type
    )


def get_call_assocs(
    data: dict, first: bool, last: bool
) -> list[TrainServiceCallAssociatedServiceInData]:
    assocs_data = data.get("associations")
    if assocs_data is None:
        return []
    return [
        assoc
        for assoc_data in assocs_data
        if (assoc := get_call_assoc(assoc_data, first, last)) is not None
    ]


def get_call_mileage(
    service_soup: BeautifulSoup, station_crs
) -> Optional[Decimal]:
    call_div = get_location_div_from_service_page(service_soup, station_crs)
    return (
        get_miles_and_chains_from_call_div(call_div)
        if call_div is not None
        else None
    )


def response_to_call(
    service_soup: Optional[BeautifulSoup],
    run_date: datetime,
    data: dict,
    first: bool,
    last: bool,
) -> TrainServiceCallInData:
    station_crs = data["crs"]
    station_name = data["description"]
    plan_arr = response_to_time(run_date, "gbttBookedArrival", data)
    plan_dep = response_to_time(run_date, "gbttBookedDeparture", data)
    act_arr = response_to_time(run_date, "realtimeArrival", data)
    act_dep = response_to_time(run_date, "realtimeDeparture", data)
    platform = data.get("platform")
    assocs = get_call_assocs(data, first, last)
    mileage = (
        get_call_mileage(service_soup, station_crs)
        if service_soup is not None
        else None
    )
    return TrainServiceCallInData(
        station_crs,
        station_name,
        platform,
        plan_arr,
        plan_dep,
        act_arr,
        act_dep,
        assocs,
        mileage,
    )


def get_service_json(service_id: str, run_date: datetime) -> Any:
    endpoint = (
        f"{service_endpoint}/{service_id}/{get_datetime_route(run_date, False)}"
    )
    rtt_credentials = get_api_credentials("RTT")
    response = make_get_request(endpoint, rtt_credentials)
    data = response.json()
    return data


@dataclass
class CallGraphNode:
    station_crs: str
    plan_arr: Optional[datetime]
    plan_dep: Optional[datetime]


CallGraph = dict[Optional[str], dict[Optional[str], list[CallGraphNode]]]


def get_call_graph_node_key(call_graph_node: CallGraphNode) -> str:
    plan_arr_string = (
        "XXXX"
        if call_graph_node.plan_arr is None
        else call_graph_node.plan_arr.strftime("%H%M")
    )
    plan_dep_string = (
        "XXXX"
        if call_graph_node.plan_dep is None
        else call_graph_node.plan_dep.strftime("%H%M")
    )
    return f"{call_graph_node.station_crs}{plan_arr_string}{plan_dep_string}"


def get_call_graph_string(
    call_graph: CallGraph, first_call: CallGraphNode
) -> str:
    call_graph_lines = []
    frontier: list[tuple[CallGraphNode, Optional[CallGraphNode], int]] = [
        (
            CallGraphNode(
                first_call.station_crs,
                first_call.plan_arr,
                first_call.plan_dep,
            ),
            None,
            0,
        )
    ]
    while len(frontier) > 0:
        current_call, previous_call, indent = frontier.pop()
        lines = "| " * (indent + 1)
        call_graph_lines.append(f"{lines}{current_call.station_crs}")
        if call_graph.get(current_call.station_crs) is None:
            continue
        next_calls = call_graph[current_call.station_crs][
            (
                get_call_graph_node_key(previous_call)
                if previous_call is not None
                else None
            )
        ]
        for i, next_call in enumerate(next_calls):
            frontier.append((next_call, current_call, indent + i))
    return "\n".join(call_graph_lines)


def merge_call_graphs(
    call_graph_a: CallGraph,
    call_graph_b: CallGraph,
    none_replacement: Optional[CallGraphNode],
) -> CallGraph:
    new_call_graph = {}
    for crs, nexts in call_graph_a.items():
        new_call_graph[crs] = nexts
    for crs, nexts in call_graph_b.items():
        call_graph_a_nexts = call_graph_a.get(crs)
        if call_graph_a_nexts is None:
            new_call_graph[crs] = nexts
        else:
            for prev_crs, next_crses in nexts.items():
                if prev_crs is None:
                    prev_crs = (
                        get_call_graph_node_key(none_replacement)
                        if none_replacement is not None
                        else None
                    )
                call_graph_a_next_crses = call_graph_a_nexts.get(prev_crs)
                if call_graph_a_next_crses is None:
                    new_call_graph[crs][prev_crs] = next_crses
                else:
                    new_call_graph[crs][prev_crs] = (
                        new_call_graph[crs][prev_crs] + next_crses
                    )
    return new_call_graph


def get_service_call_associated_services(
    current_service_uid: str,
    current_service_run_date: datetime,
    parent_service_uid: Optional[str],
    parent_service_run_date: Optional[datetime],
    call: TrainServiceCallInData,
) -> list[tuple[TrainServiceInData, CallGraph, AssociatedType]]:
    associated_services = []
    for assoc in call.assocs:
        if (
            assoc.service_unique_identifier == parent_service_uid
            and assoc.service_run_date == parent_service_run_date
        ):
            continue
        assoc_service = get_service_from_id(
            assoc.service_unique_identifier,
            assoc.service_run_date,
            current_service_uid,
            current_service_run_date,
        )
        if assoc_service is None:
            continue
        assoc_services, assoc_call_graph = assoc_service
        associated_services.append(
            (assoc_services, assoc_call_graph, assoc.association)
        )
    return associated_services


def get_service_from_id(
    service_id: str,
    run_date: datetime,
    parent_service_uid: Optional[str] = None,
    parent_service_run_date: Optional[datetime] = None,
    soup: bool = False,
) -> Optional[tuple[list[TrainServiceInData], CallGraph]]:
    data = get_service_json(service_id, run_date)
    services = []
    if not data.get("isPassenger") and not data.get("serviceType") == "train":
        return None
    headcode = data["trainIdentity"]
    power = data.get("powerType")
    origins = [origin["description"] for origin in data["origin"]]
    destinations = [
        destination["description"] for destination in data["destination"]
    ]
    operator_code = data["atocCode"]
    calls: list[TrainServiceCallInData] = []
    if soup:
        service_soup = get_service_page(service_id, run_date)
    else:
        service_soup = None
    call_graph = {}
    call_grandparent = None
    call_parent = None
    for i, loc in enumerate(data["locations"]):
        if loc.get("crs") is None:
            continue
        call = response_to_call(
            service_soup, run_date, loc, i == 0, i == len(data["locations"]) - 1
        )
        call_graph_node = CallGraphNode(
            call.station_crs, call.plan_arr, call.plan_dep
        )

        call_grandparent_key = (
            get_call_graph_node_key(call_grandparent)
            if call_grandparent is not None
            else None
        )
        call_parent_key = (
            call_parent.station_crs if call_parent is not None else None
        )
        if call_graph.get(call_parent_key) is None:
            call_graph[call_parent_key] = {}
        if call_graph[call_parent_key].get(call_grandparent_key) is None:
            call_graph[call_parent_key][call_grandparent_key] = [
                call_graph_node
            ]
        else:
            call_graph[call_parent_key][call_grandparent_key].append(
                call_graph_node
            )
        assoc_services = get_service_call_associated_services(
            service_id,
            run_date,
            parent_service_uid,
            parent_service_run_date,
            call,
        )
        for assoc_service, assoc_call_graph, assoc_type in assoc_services:
            if assoc_type == AssociatedType.OTHER_DIVIDES:
                none_replacement = CallGraphNode(
                    call.station_crs, call.plan_arr, call.plan_dep
                )
            else:
                none_replacement = None
            call_graph = merge_call_graphs(
                call_graph, assoc_call_graph, none_replacement
            )
            services.append(assoc_service)
        calls = calls + [call]
        call_grandparent = call_parent
        call_parent = CallGraphNode(
            call.station_crs, call.plan_arr, call.plan_dep
        )
    train_service = TrainServiceInData(
        service_id,
        run_date,
        headcode,
        origins,
        destinations,
        operator_code,
        None,
        power,
        calls,
    )
    services = [train_service] + services
    return (services, call_graph)


def get_service_page_url(id: str, service_date: datetime) -> str:
    date_string = service_date.strftime("%Y-%m-%d")
    return f"https://www.realtimetrains.co.uk/service/gb-nr:{id}/{date_string}/detailed"


def get_service_page_url_from_service(service: TrainServiceInData) -> str:
    return get_service_page_url(service.unique_identifier, service.run_date)


def get_service_page(
    service_id: str, run_date: datetime
) -> Optional[BeautifulSoup]:
    url = get_service_page_url(service_id, run_date)
    soup = get_soup(url)
    return soup


def get_service_page_from_service(
    service: TrainServiceInData,
) -> Optional[BeautifulSoup]:
    get_service_page(service.unique_identifier, service.run_date)


def get_location_div_from_service_page(
    service_soup: BeautifulSoup, crs: str
) -> Optional[Tag]:
    calls = service_soup.find_all(class_="call")
    for call in calls:
        if isinstance(call, Tag) and crs.upper() in call.get_text():
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

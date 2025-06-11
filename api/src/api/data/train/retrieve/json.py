from datetime import datetime, timedelta
from typing import Any, Optional

from api.data.train.association import AssociationType
from api.data.train.retrieve.html import (
    get_call_mileage_from_service_soup,
    get_train_service_soup,
)
from api.data.train.retrieve.insert import (
    TrainAssociatedServiceInData,
    TrainServiceCallAssociatedServiceInData,
    TrainServiceCallInData,
    TrainServiceInData,
)
from api.utils.credentials import get_api_credentials
from api.utils.request import make_get_request
from api.utils.times import get_datetime_route, make_timezone_aware
from bs4 import BeautifulSoup


service_endpoint = "https://api.rtt.io/api/v1/json/service"


def get_service_json(service_id: str, run_date: datetime) -> Any:
    endpoint = (
        f"{service_endpoint}/{service_id}/{get_datetime_route(run_date, False)}"
    )
    rtt_credentials = get_api_credentials("RTT")
    response = make_get_request(endpoint, rtt_credentials)
    data = response.json()
    return data


def get_datetime_from_service_json(
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


def get_associated_service_from_associated_service_json(
    associated_service_json: dict,
    first: bool,
    last: bool,
    service_uid: str,
    service_run_date: datetime,
    parent_uid: Optional[str],
    parent_run_date: Optional[datetime],
) -> Optional[TrainServiceCallAssociatedServiceInData]:
    assoc_uid = associated_service_json["associatedUid"]
    assoc_date = datetime.strptime(
        associated_service_json["associatedRunDate"], "%Y-%m-%d"
    )

    if (
        parent_uid is not None
        and parent_run_date is not None
        and (assoc_uid == parent_uid and assoc_date == parent_run_date)
    ):
        return None

    associated_service = get_service_from_id(
        assoc_uid, assoc_date, service_uid, service_run_date
    )
    if associated_service is None:
        return None

    if associated_service_json["type"] == "divide":
        if first:
            assoc_type = AssociationType.THIS_DIVIDES
        else:
            assoc_type = AssociationType.OTHER_DIVIDES
    elif associated_service_json["type"] == "join":
        if last:
            assoc_type = AssociationType.THIS_JOINS
        else:
            assoc_type = AssociationType.OTHER_DIVIDES
    else:
        return None

    return TrainServiceCallAssociatedServiceInData(
        associated_service, assoc_type
    )


def get_associated_services_from_call_json(
    call_json: dict,
    is_first_call: bool,
    is_last_call: bool,
    service_uid: str,
    service_run_date: datetime,
    parent_service_uid: Optional[str],
    parent_service_run_date: Optional[datetime],
) -> list[TrainServiceCallAssociatedServiceInData]:
    assocs_data = call_json.get("associations")
    if assocs_data is None:
        return []
    return [
        assoc
        for assoc_data in assocs_data
        if (
            assoc := get_associated_service_from_associated_service_json(
                assoc_data,
                is_first_call,
                is_last_call,
                service_uid,
                service_run_date,
                parent_service_uid,
                parent_service_run_date,
            )
        )
        is not None
    ]


def get_datetime_from_json_field(
    run_date: datetime, field_name: str, json: dict
) -> Optional[datetime]:
    time_string = json.get(field_name)
    if time_string is None:
        return None
    next_day = json.get(f"{field_name}NextDay")
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


def get_call_from_call_json(
    call_json: dict,
    service_soup: Optional[BeautifulSoup],
    is_first_call: bool,
    is_last_call: bool,
    service_uid: str,
    service_run_date: datetime,
    parent_service_uid: Optional[str],
    parent_service_run_date: Optional[datetime],
) -> TrainServiceCallInData:
    station_crs = call_json["crs"]
    station_name = call_json["description"]
    plan_arr = get_datetime_from_json_field(
        service_run_date, "gbttBookedArrival", call_json
    )
    plan_dep = get_datetime_from_json_field(
        service_run_date, "gbttBookedDeparture", call_json
    )
    act_arr = get_datetime_from_json_field(
        service_run_date, "realtimeArrival", call_json
    )
    act_dep = get_datetime_from_json_field(
        service_run_date, "realtimeDeparture", call_json
    )
    platform = call_json.get("platform")
    associated_services = get_associated_services_from_call_json(
        call_json,
        is_first_call,
        is_last_call,
        service_uid,
        service_run_date,
        parent_service_uid,
        parent_service_run_date,
    )
    mileage = (
        get_call_mileage_from_service_soup(
            service_soup, station_crs, plan_arr, plan_dep
        )
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
        associated_services,
        mileage,
    )


def get_service_calls_from_service_json(
    service_uid: str,
    service_run_date: datetime,
    service_json: dict,
    service_soup: Optional[BeautifulSoup],
    parent_service_uid: Optional[str],
    parent_service_run_date: Optional[datetime],
) -> list[TrainServiceCallInData]:
    calls: list[TrainServiceCallInData] = []
    associated_services: list[TrainAssociatedServiceInData] = []
    for i, call_json in enumerate(service_json["locations"]):
        if call_json.get("crs") is None:
            continue
        is_first_call = i == 0
        is_last_call = i == len(service_json["locations"]) - 1
        call = get_call_from_call_json(
            call_json,
            service_soup,
            is_first_call,
            is_last_call,
            service_uid,
            service_run_date,
            parent_service_uid,
            parent_service_run_date,
        )
        calls.append(call)
        service_associated_services = [
            TrainAssociatedServiceInData(
                associated_service.associated_service,
                call.plan_arr,
                call.act_arr,
                call.plan_dep,
                call.act_dep,
                associated_service.association,
            )
            for associated_service in call.associated_services
        ]
        associated_services.extend(service_associated_services)
    return calls


def get_service_from_service_json_and_html(
    service_uid: str,
    service_run_date: datetime,
    service_json: dict,
    service_soup: Optional[BeautifulSoup],
    parent_service_uid: Optional[str],
    parent_service_run_date: Optional[datetime],
) -> Optional[TrainServiceInData]:
    if (
        not service_json.get("isPassenger")
        and not service_json.get("serviceType") == "train"
    ):
        return None
    headcode = service_json["trainIdentity"]
    power = service_json.get("powerType")
    origins = [origin["description"] for origin in service_json["origin"]]
    destinations = [
        destination["description"]
        for destination in service_json["destination"]
    ]
    operator_code = service_json["atocCode"]
    calls = get_service_calls_from_service_json(
        service_uid,
        service_run_date,
        service_json,
        service_soup,
        parent_service_uid,
        parent_service_run_date,
    )
    train_service = TrainServiceInData(
        service_uid,
        service_run_date,
        headcode,
        origins,
        destinations,
        operator_code,
        None,
        power,
        calls,
    )
    return train_service


def get_service_from_id(
    service_uid: str,
    service_run_date: datetime,
    parent_service_uid: Optional[str] = None,
    parent_service_run_date: Optional[datetime] = None,
    scrape_html: bool = False,
) -> Optional[TrainServiceInData]:
    service_json = get_service_json(service_uid, service_run_date)
    if scrape_html:
        service_html = get_train_service_soup(service_uid, service_run_date)
    else:
        service_html = None
    return get_service_from_service_json_and_html(
        service_uid,
        service_run_date,
        service_json,
        service_html,
        parent_service_uid,
        parent_service_run_date,
    )

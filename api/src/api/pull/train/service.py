from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from bs4 import BeautifulSoup, Tag
from psycopg import Connection

from api.classes.interactive import PickSingle
from api.classes.train.association import AssociationType
from api.db.functions.select.train.operator import (
    select_train_operator_by_operator_code_fetchone,
)
from api.db.types.train.operator import TrainOperatorOutData
from api.pull.train.types import (
    RttCallAssociatedService,
    RttLocationTag,
    RttService,
    RttServiceAssociatedService,
    RttServiceCall,
)
from api.utils.credentials import get_api_credentials
from api.utils.interactive import input_select
from api.utils.mileage import miles_and_chains_to_miles
from api.utils.request import get_soup, make_get_request
from api.utils.soup import get_tag_by_class_name, get_tags_by_class_name
from api.utils.times import get_datetime_route, make_timezone_aware

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
    run_date: datetime, time_field: str, data: dict[str, Any]
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


def get_associated_service_from_call_associated_service_json(
    conn: Connection,
    associated_service_json: dict[str, Any],
    first: bool,
    last: bool,
    service_uid: str,
    service_run_date: datetime,
    parent_uid: Optional[str],
    parent_run_date: Optional[datetime],
    service_operator: TrainOperatorOutData,
    brand_id: Optional[int],
) -> Optional[RttCallAssociatedService]:
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
        conn,
        assoc_uid,
        assoc_date,
        service_uid,
        service_run_date,
        service_operator=service_operator,
        brand_id=brand_id,
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

    return RttCallAssociatedService(associated_service, assoc_type)


def get_associated_services_from_call_json(
    conn: Connection,
    call_json: dict[str, Any],
    is_first_call: bool,
    is_last_call: bool,
    service_uid: str,
    service_run_date: datetime,
    parent_service_uid: Optional[str],
    parent_service_run_date: Optional[datetime],
    service_operator: TrainOperatorOutData,
    brand_id: Optional[int],
) -> list[RttCallAssociatedService]:
    assocs_data = call_json.get("associations")
    if assocs_data is None:
        return []
    return [
        assoc
        for assoc_data in assocs_data
        if (
            assoc := get_associated_service_from_call_associated_service_json(
                conn,
                assoc_data,
                is_first_call,
                is_last_call,
                service_uid,
                service_run_date,
                parent_service_uid,
                parent_service_run_date,
                service_operator,
                brand_id=brand_id,
            )
        )
        is not None
    ]


def get_datetime_from_json_field(
    run_date: datetime, field_name: str, json: dict[str, Any]
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
    conn: Connection,
    call_json: dict[str, Any],
    service_soup: Optional[BeautifulSoup],
    is_first_call: bool,
    is_last_call: bool,
    service_uid: str,
    service_run_date: datetime,
    parent_service_uid: Optional[str],
    parent_service_run_date: Optional[datetime],
    service_operator: TrainOperatorOutData,
    brand_id: Optional[int],
    rtt_location_tags: Optional[list[RttLocationTag]],
) -> RttServiceCall:
    station_crs = call_json["crs"]
    station_name = call_json["description"]
    plan_arr = get_datetime_from_json_field(
        service_run_date, "gbttBookedArrival", call_json
    )
    act_arr = get_datetime_from_json_field(
        service_run_date, "realtimeArrival", call_json
    )
    plan_dep = get_datetime_from_json_field(
        service_run_date, "gbttBookedDeparture", call_json
    )
    act_dep = get_datetime_from_json_field(
        service_run_date, "realtimeDeparture", call_json
    )
    platform = call_json.get("platform")
    associated_services = get_associated_services_from_call_json(
        conn,
        call_json,
        is_first_call,
        is_last_call,
        service_uid,
        service_run_date,
        parent_service_uid,
        parent_service_run_date,
        service_operator,
        brand_id=brand_id,
    )
    mileage = (
        get_call_mileage_from_service_soup(
            rtt_location_tags, station_crs, plan_arr, plan_dep
        )
        if rtt_location_tags is not None
        else None
    )
    return RttServiceCall(
        station_crs,
        station_name,
        platform,
        plan_arr,
        act_arr,
        plan_dep,
        act_dep,
        associated_services,
        mileage,
    )


def get_service_calls_from_service_json(
    conn: Connection,
    service_uid: str,
    service_run_date: datetime,
    service_json: dict[str, Any],
    service_soup: Optional[BeautifulSoup],
    parent_service_uid: Optional[str],
    parent_service_run_date: Optional[datetime],
    service_operator: TrainOperatorOutData,
    brand_id: Optional[int] = None,
) -> tuple[list[RttServiceCall], list[RttServiceAssociatedService]]:
    calls: list[RttServiceCall] = []
    associated_services: list[RttServiceAssociatedService] = []
    if service_soup is not None:
        rtt_location_tags = get_rtt_location_tags_from_service_page(
            service_soup
        )
    else:
        rtt_location_tags = None
    for i, call_json in enumerate(service_json["locations"]):
        if call_json.get("crs") is None:
            continue
        is_first_call = i == 0
        is_last_call = i == len(service_json["locations"]) - 1
        call = get_call_from_call_json(
            conn,
            call_json,
            service_soup,
            is_first_call,
            is_last_call,
            service_uid,
            service_run_date,
            parent_service_uid,
            parent_service_run_date,
            service_operator=service_operator,
            brand_id=brand_id,
            rtt_location_tags=rtt_location_tags,
        )
        calls.append(call)
        service_associated_services = [
            RttServiceAssociatedService(
                associated_service.service,
                call,
                associated_service.association,
            )
            for associated_service in call.associated_services
        ]
        associated_services.extend(service_associated_services)
    return calls, associated_services


def get_brand_code_id_input(operator: TrainOperatorOutData) -> Optional[int]:
    if len(operator.operator_brands) == 0:
        return None
    elif len(operator.operator_brands) == 1:
        return operator.operator_brands[0].brand_id
    else:
        match input_select(
            "Select brand",
            operator.operator_brands,
            lambda b: f"{b.brand_name} ({b.brand_code})",
        ):
            case PickSingle(brand):
                return brand.brand_id
            case _:
                return None


def get_service_from_service_json_and_html(
    conn: Connection,
    service_json: dict[str, Any],
    service_soup: Optional[BeautifulSoup],
    parent_service_uid: Optional[str],
    parent_service_run_date: Optional[datetime],
    service_operator: Optional[TrainOperatorOutData] = None,
    brand_id: Optional[int] = None,
    query_brand: bool = False,
) -> Optional[RttService]:
    if (
        not service_json.get("isPassenger")
        or not service_json.get("serviceType") == "train"
    ):
        return None
    service_uid = service_json["serviceUid"]
    service_run_date = datetime.strptime(service_json["runDate"], "%Y-%m-%d")
    headcode = service_json["trainIdentity"]
    power = service_json.get("powerType")
    origins = [origin["description"] for origin in service_json["origin"]]
    destinations = [
        destination["description"]
        for destination in service_json["destination"]
    ]
    operator_code = service_json["atocCode"]
    if (
        service_operator is None
        or service_operator.operator_code != operator_code
    ):
        operator_data = select_train_operator_by_operator_code_fetchone(
            conn, operator_code, service_run_date
        )
        if operator_data is None:
            raise RuntimeError(
                f"Could not get operator for code {operator_code}"
            )
    else:
        operator_data = service_operator
    if brand_id is None and query_brand:
        brand_id = get_brand_code_id_input(operator_data)
    calls, associated_services = get_service_calls_from_service_json(
        conn,
        service_uid,
        service_run_date,
        service_json,
        service_soup,
        parent_service_uid,
        parent_service_run_date,
        service_operator=operator_data,
        brand_id=brand_id,
    )
    train_service = RttService(
        service_uid,
        service_run_date,
        headcode,
        origins,
        destinations,
        operator_data.operator_id,
        brand_id,
        power,
        calls,
        associated_services,
    )
    return train_service


def get_service_from_id(
    conn: Connection,
    service_uid: str,
    service_run_date: datetime,
    parent_service_uid: Optional[str] = None,
    parent_service_run_date: Optional[datetime] = None,
    scrape_html: bool = False,
    service_operator: Optional[TrainOperatorOutData] = None,
    brand_id: Optional[int] = None,
    query_brand: bool = False,
) -> Optional[RttService]:
    service_json = get_service_json(service_uid, service_run_date)
    if scrape_html:
        service_html = get_train_service_soup(service_uid, service_run_date)
    else:
        service_html = None
    return get_service_from_service_json_and_html(
        conn,
        service_json,
        service_html,
        parent_service_uid,
        parent_service_run_date,
        service_operator=service_operator,
        brand_id=brand_id,
        query_brand=query_brand,
    )


def get_service_page_url(id: str, service_date: datetime) -> str:
    date_string = service_date.strftime("%Y-%m-%d")
    return f"https://www.realtimetrains.co.uk/service/gb-nr:{id}/{date_string}/detailed"


def get_train_service_soup(
    service_id: str, run_date: datetime
) -> Optional[BeautifulSoup]:
    url = get_service_page_url(service_id, run_date)
    soup = get_soup(url)
    return soup


def get_rtt_location_tag_from_service_page_call_div(
    call: Tag,
) -> Optional[RttLocationTag]:
    call_distance = get_tag_by_class_name(call, "distance")

    if call_distance is None:
        call_distance_value = None
    else:
        call_distance_miles = get_tag_by_class_name(call_distance, "miles")
        call_distance_chains = get_tag_by_class_name(call_distance, "chains")

        if call_distance_miles is None or call_distance_chains is None:
            call_distance_value = None
        else:
            call_distance_miles_value = int(call_distance_miles.get_text())
            call_distance_chains_value = int(call_distance_chains.get_text())
            call_distance_value = miles_and_chains_to_miles(
                call_distance_miles_value, call_distance_chains_value
            )

    call_location = get_tag_by_class_name(call, "location")

    if call_location is None:
        return None
    else:
        call_location_split = call_location.get_text().split("[")
        if len(call_location_split) != 2:
            return None
        else:
            call_location_crs_value = call_location_split[1][0:3]

    call_gbtt = get_tag_by_class_name(call, "gbtt")

    if call_gbtt is None:
        return None
    else:
        call_gbtt_arr = get_tag_by_class_name(call_gbtt, "arr")

        if call_gbtt_arr is None:
            call_gbtt_arr_value = None
        else:
            call_gbtt_arr_text = call_gbtt_arr.get_text()
            if call_gbtt_arr_text == "":
                call_gbtt_arr_value = None
            else:
                call_gbtt_arr_value = datetime.strptime(
                    call_gbtt_arr_text, "%H%M"
                )

        call_gbtt_dep = get_tag_by_class_name(call_gbtt, "dep")

        if call_gbtt_dep is None:
            call_gbtt_dep_value = None
        else:
            call_gbtt_dep_text = call_gbtt_dep.get_text()
            if call_gbtt_dep_text == "":
                call_gbtt_dep_value = None
            else:
                call_gbtt_dep_value = datetime.strptime(
                    call_gbtt_dep_text, "%H%M"
                )

    return RttLocationTag(
        call_distance_value,
        call_location_crs_value,
        call_gbtt_arr_value,
        call_gbtt_dep_value,
    )


def get_rtt_location_tags_from_service_page(
    service_soup: BeautifulSoup,
) -> list[RttLocationTag]:
    calls = get_tags_by_class_name(service_soup, "call")
    return [
        rtt_location_tag
        for call in calls
        if (
            rtt_location_tag := get_rtt_location_tag_from_service_page_call_div(
                call
            )
        )
        is not None
    ]


def get_rtt_location_tag_from_list(
    rtt_location_tags: list[RttLocationTag],
    crs: str,
    plan_arr: Optional[datetime],
    plan_dep: Optional[datetime],
) -> Optional[RttLocationTag]:
    for rtt_location_tag in rtt_location_tags:
        if rtt_location_tag.crs.upper() != crs:
            continue
        if plan_arr is not None and (
            rtt_location_tag.gbtt_arr is None
            or rtt_location_tag.gbtt_arr.hour != plan_arr.hour
            and rtt_location_tag.gbtt_arr.minute != plan_arr.minute
        ):
            continue
        if plan_dep is not None and (
            rtt_location_tag.gbtt_dep is None
            or rtt_location_tag.gbtt_dep.hour != plan_dep.hour
            and rtt_location_tag.gbtt_dep.minute != plan_dep.minute
        ):
            continue
        return rtt_location_tag
    return None


def get_call_mileage_from_service_soup(
    rtt_location_tags: list[RttLocationTag],
    station_crs: str,
    plan_arr: Optional[datetime],
    plan_dep: Optional[datetime],
) -> Optional[Decimal]:
    rtt_location_tag = get_rtt_location_tag_from_list(
        rtt_location_tags, station_crs, plan_arr, plan_dep
    )
    return rtt_location_tag.mileage if rtt_location_tag is not None else None

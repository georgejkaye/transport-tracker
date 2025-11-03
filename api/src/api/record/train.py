import json
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional, Tuple

from psycopg import Connection

from api.classes.train.association import (
    AssociationType,
    int_of_association_type,
)
from api.classes.train.stock import (
    sort_by_classes,
    sort_by_subclasses,
    string_of_class,
    string_of_class_and_subclass,
    string_of_stock_report,
)
from api.db.functions.insert.train.leg import insert_train_leg_fetchone
from api.db.functions.select.train.station import (
    select_train_station_by_crs_fetchone,
    select_train_stations_by_name_substring_fetchall,
)
from api.db.functions.select.train.stock import (
    select_train_operator_stock_fetchall,
)
from api.db.types.register import register_types
from api.db.types.train.leg import (
    TrainLegAssociatedServiceInData,
    TrainLegCallCallInData,
    TrainLegCallInData,
    TrainLegInData,
    TrainLegServiceCallInData,
    TrainLegServiceEndpointInData,
    TrainLegServiceInData,
    TrainLegStockSegmentInData,
    TrainLegStockSegmentReportInData,
)
from api.db.types.train.station import TrainStationOutData
from api.db.types.train.stock import (
    TrainStockOutData,
    TrainStockSubclassOutData,
)
from api.pull.train.service import get_service_from_id
from api.pull.train.station import get_services_at_station
from api.pull.train.types import (
    RttService,
    RttServiceCall,
    RttStationService,
    RttStationServiceToDestination,
    TrainStationIdentifiers,
)
from api.record.user import input_users
from api.utils.database import connect_with_env
from api.utils.debug import debug_msg
from api.utils.interactive import (
    PickMultiple,
    PickSingle,
    PickUnknown,
    information,
    input_checkbox,
    input_confirm,
    input_datetime,
    input_number,
    input_select,
    input_select_paginate,
    input_text,
)
from api.utils.mileage import (
    miles_and_chains_to_miles,
    string_of_miles_and_chains,
)
from api.utils.times import (
    add,
    get_hourmin_string,
    make_timezone_aware,
)


def timedelta_from_string(string: str) -> timedelta:
    parts = string.split(":")
    hour = int(parts[0])
    minutes = int(parts[1])
    return timedelta(hours=hour, minutes=minutes)


def get_station_from_input(
    conn: Connection, prompt: str, stn: TrainStationOutData | None = None
) -> Optional[TrainStationOutData]:
    """
    Get a string specifying a station from a user.
    Can either be a three letter code (in which case confirmation will be asked for)
    or a full station name
    """
    if stn is not None:
        full_prompt = f"{prompt} ({stn.station_name})"
        default = stn.station_crs
    else:
        full_prompt = prompt
        default = ""
    while True:
        input_string_opt = input_text(full_prompt, default=default)
        if input_string_opt is None:
            return None
        input_string = input_string_opt.lower()
        # We only search for strings of length at least three, otherwise there would be loads
        if len(input_string) == 0 and stn is not None:
            return stn
        if len(input_string) == 3:
            crs_station = select_train_station_by_crs_fetchone(
                conn, input_string
            )
            if crs_station is not None:
                resp = input_confirm(f"Did you mean {crs_station.station_name}")
                if resp:
                    return crs_station
        # Otherwise search for substrings in the full names of stations
        matches = select_train_stations_by_name_substring_fetchall(
            conn, input_string
        )
        if len(matches) == 0:
            print("No matches found, try again")
        elif len(matches) == 1:
            match = matches[0]
            resp = input_confirm(f"Did you mean {match.station_name}?")
            if resp:
                return match
        else:
            print("Multiple matches found: ")
            choice = input_select_paginate(
                "Select a station",
                matches,
                display=lambda x: x.station_name,
            )
            match choice:
                case PickSingle(stn):
                    return stn
                case _:
                    return None


def string_of_service_at_station_to_destination(
    service: RttStationServiceToDestination,
) -> str:
    return f"{service.headcode} {get_multiple_short_station_string(service.origins)} to {get_multiple_short_station_string(service.destinations)} plan {get_hourmin_string(service.plan_dep)} act {get_hourmin_string(service.act_dep)} ({service.operator_code})"


def get_service_at_station(
    conn: Connection,
    origin: TrainStationOutData,
    search_datetime: datetime,
    destination: TrainStationOutData,
) -> Optional[RttStationServiceToDestination]:
    """
    Record a new journey in the logfile
    """
    origin_services = get_services_at_station(conn, origin, search_datetime)
    # We want to search within a smaller timeframe
    timeframe = 15
    earliest_time = add(search_datetime, -timeframe)
    latest_time = add(search_datetime, timeframe)
    information("Searching for services from " + origin.station_name)
    # The results encompass a ~1 hour period
    # We only want to check our given timeframe
    # We also only want services that stop at our destination
    filtered_services = filter_services_by_time_and_stop(
        earliest_time, latest_time, origin, destination, origin_services
    )
    if len(filtered_services) == 0:
        return None
    choice = input_select_paginate(
        "Pick a service",
        filtered_services,
        display=string_of_service_at_station_to_destination,
    )
    match choice:
        case PickSingle(service):
            return service
        case _:
            return None


def get_unit_class(
    operator_stock: list[TrainStockOutData],
) -> Optional[PickUnknown | PickSingle[TrainStockOutData]]:
    chosen_class = input_select(
        "Class number",
        sort_by_classes(operator_stock),
        unknown=True,
        display=string_of_class,
    )
    match chosen_class:
        case None:
            return None
        case PickUnknown():
            return chosen_class
        case PickSingle(_):
            return chosen_class
        case _:
            return None


def get_unit_subclass(
    stock: TrainStockOutData,
) -> Optional[PickUnknown | PickSingle[TrainStockSubclassOutData]]:
    if len(stock.stock_subclasses) == 1:
        return PickSingle(stock.stock_subclasses[0])
    else:
        chosen_subclass = input_select(
            "Subclass no",
            sort_by_subclasses(stock.stock_subclasses),
            unknown=True,
            cancel=False,
            display=lambda c: string_of_class_and_subclass(stock, c),
        )
        match chosen_subclass:
            case None:
                return None
            case PickUnknown():
                return chosen_subclass
            case PickSingle(_):
                return chosen_subclass
            case _:
                return None


def get_unit_no(
    stock_class: TrainStockOutData, stock_subclass: TrainStockSubclassOutData
) -> Optional[int]:
    while True:
        unit_no_opt = input_number(
            "Stock number",
            lower=stock_class.stock_class * 1000,
            upper=stock_class.stock_class * 1000 + 999,
            unknown=True,
        )
        return unit_no_opt


def get_unit_cars(
    stock_class: TrainStockOutData,
    stock_subclass: TrainStockSubclassOutData,
) -> PickUnknown | PickSingle[int] | None:
    if len(stock_subclass.stock_cars) == 1:
        information(
            f"{string_of_class_and_subclass(stock_class, stock_subclass, name=False)} always has {stock_subclass.stock_cars[0]} cars"
        )
        return PickSingle(stock_subclass.stock_cars[0])
    result = input_select(
        "Number of cars",
        stock_subclass.stock_cars,
        lambda c: f"{c} car{'s' if c > 1 else ''}",
        unknown=True,
    )
    match result:
        case None:
            return None
        case PickUnknown():
            return result
        case PickSingle(_):
            return result
        case _:
            return None


def input_station_from_calls(
    current: TrainLegCallInData,
    calls: list[TrainLegCallInData],
) -> Optional[Tuple[TrainLegCallInData, int, list[TrainLegCallInData]]]:
    end_call = input_select_paginate(
        f"Stock formation from {current.station_name} until",
        [(i, call) for (i, call) in enumerate(calls)],
        display=lambda x: f"{x[1].station_name} ({x[1].station_crs})",
    )
    match end_call:
        case PickSingle((i, call)):
            return (call, i, calls[i + 1 :])
        case PickUnknown():
            return None
        case _:
            raise RuntimeError()


StockChange = Enum("StockChange", ["GAIN", "LOSE"])


def string_of_stock_change(change: StockChange) -> str:
    match change:
        case StockChange.GAIN:
            return "Gain units"
        case StockChange.LOSE:
            return "Lose units"


def get_unit_report(
    stock_list: list[TrainStockOutData],
) -> Optional[TrainLegStockSegmentReportInData]:
    stock_class_res = get_unit_class(stock_list)
    stock_class: Optional[TrainStockOutData] = None
    stock_subclass: Optional[TrainStockSubclassOutData] = None
    match stock_class_res:
        case None:
            return None
        case PickSingle(stock_class_choice):
            stock_class = stock_class_choice
        case _:
            stock_class = None
            stock_subclass = None
    if stock_class is not None:
        stock_subclass_res = get_unit_subclass(stock_class)
        match stock_subclass_res:
            case None:
                return None
            case PickUnknown():
                stock_subclass = None
            case PickSingle(stock_subclass_choice):
                stock_subclass = stock_subclass_choice
    else:
        stock_subclass = None
    if stock_class is not None and stock_subclass is not None:
        stock_unit_no = get_unit_no(stock_class, stock_subclass)
        stock_cars_res = get_unit_cars(stock_class, stock_subclass)
        match stock_cars_res:
            case None:
                return None
            case PickUnknown():
                stock_cars = None
            case PickSingle(form):
                stock_cars = form
    else:
        stock_unit_no = None
        stock_cars = None
    return TrainLegStockSegmentReportInData(
        stock_class.stock_class if stock_class is not None else None,
        stock_subclass.stock_subclass if stock_subclass is not None else None,
        stock_unit_no,
        stock_cars,
    )


def get_stock_change_reason(
    previous_stock_segment: Optional[TrainLegStockSegmentInData],
) -> StockChange:
    if previous_stock_segment is None:
        return StockChange.GAIN
    result = input_select(
        "Pick reason for stock change",
        [StockChange.GAIN, StockChange.LOSE],
        display=string_of_stock_change,
    )
    match result:
        case PickSingle(stock_change):
            return stock_change
        case _:
            raise RuntimeError()


def get_stock_from_previous_stock_segment(
    previous_stock_segment: Optional[TrainLegStockSegmentInData],
) -> list[TrainLegStockSegmentReportInData]:
    return (
        previous_stock_segment.stock_reports
        if previous_stock_segment is not None
        else []
    )


def get_stock(
    conn: Connection,
    calls: list[TrainLegCallInData],
    service: RttService,
    stock_number: int = 0,
) -> list[TrainLegStockSegmentInData]:
    information("Recording stock formations")
    stock_segments: list[TrainLegStockSegmentInData] = []
    previous_stock_segment: Optional[TrainLegStockSegmentInData] = None
    # Currently getting this automatically isn't implemented
    stock_list = select_train_operator_stock_fetchall(
        conn, service.operator_id, service.brand_id, service.run_date
    )
    current_call = calls[0]
    remaining_calls = calls[1:]
    while len(remaining_calls) > 0:
        information(
            f"Recording stock formation after {current_call.station_name}"
        )
        segment_start = current_call
        next_remaining_calls: list[TrainLegCallInData] = []

        stock_end_opt = input_station_from_calls(segment_start, remaining_calls)
        if stock_end_opt is None:
            segment_end = remaining_calls[-1]
            segment_end_index = len(calls) - 1
        else:
            (_, segment_end_index, next_remaining_calls) = stock_end_opt
        stock_calls = [current_call] + remaining_calls[
            0 : segment_end_index + 1
        ]
        remaining_calls = next_remaining_calls
        segment_end = stock_calls[-1]
        stock_change = get_stock_change_reason(previous_stock_segment)
        previous_stock_segment_stock = get_stock_from_previous_stock_segment(
            previous_stock_segment
        )
        current_segment_stock: list[TrainLegStockSegmentReportInData] = []
        match stock_change:
            case StockChange.GAIN:
                number_of_units = input_number("Number of new units")
                if number_of_units is None:
                    return []
                for i in range(0, number_of_units):
                    information(f"Selecting unit {i + 1}")
                    stock_report = get_unit_report(stock_list)
                    if stock_report is None:
                        return []
                    current_segment_stock = previous_stock_segment_stock
                    current_segment_stock.append(stock_report)
            case StockChange.LOSE:
                result = input_checkbox(
                    "Which units remain",
                    previous_stock_segment_stock,
                    string_of_stock_report,
                )
                match result:
                    case None:
                        return []
                    case PickMultiple(choices):
                        current_segment_stock = choices
        stock_mileage = get_mileage(stock_calls)
        segment_start_call = stock_calls[0]
        segment_end_call = stock_calls[-1]
        if (
            segment_start_call.dep_call is None
            or segment_end_call.arr_call is None
        ):
            raise RuntimeError("Could not get segment endpoints")
        segment = TrainLegStockSegmentInData(
            current_segment_stock,
            segment_start_call.dep_call.service_uid,
            segment_start_call.dep_call.service_run_date,
            segment_start_call.station_crs,
            segment_start_call.dep_call.plan_dep,
            segment_start_call.dep_call.act_dep,
            segment_end_call.arr_call.service_uid,
            segment_end_call.arr_call.service_run_date,
            segment_end_call.station_crs,
            segment_end_call.arr_call.plan_arr,
            segment_end_call.arr_call.act_arr,
            stock_mileage,
        )
        stock_segments.append(segment)
        previous_stock_segment = segment
        information(
            f"Stock formation {len(stock_segments) + stock_number} recorded"
        )
        current_call = segment_end
    return stock_segments


def input_mileage(calls: list[TrainLegCallInData]) -> Decimal:
    information(
        f"Manual mileage input between {calls[0].station_name} and {calls[-1].station_name} required"
    )
    # If we can get a good distance set this could be automated
    miles = input_number("Miles")
    chains = input_number("Chains", upper=79)
    if miles is None or chains is None:
        raise RuntimeError("Cannot be None")
    return miles_and_chains_to_miles(miles, chains)


def get_mileage(calls: list[TrainLegCallInData]) -> Decimal:
    end_mileage = calls[-1].mileage
    if end_mileage is None:
        return input_mileage(calls)
    return end_mileage


def filter_services_by_time(
    earliest: datetime, latest: datetime, services: list[RttStationService]
) -> list[RttStationService]:
    filtered_services: list[RttStationService] = []
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


def get_calls_at_station(
    service: RttService, station_crs: str
) -> list[RttServiceCall]:
    matching_calls: list[RttServiceCall] = []
    for call in service.calls:
        if call.station_crs == station_crs:
            matching_calls.append(call)
    return matching_calls


def get_leg_calls_between_calls(
    service: RttService,
    start_station_crs: str,
    start_dep_time: datetime,
    end_station_crs: str,
    first_call_mileage: Decimal = Decimal(0),
) -> Optional[list[TrainLegCallInData]]:
    start_dep_time = make_timezone_aware(start_dep_time)
    leg_calls: list[TrainLegCallInData] = []
    boarded = False
    board_call_mileage: Optional[Decimal] = Decimal(0)
    for call in service.calls:
        if not boarded:
            if (
                call.station_crs == start_station_crs
                and call.plan_dep == start_dep_time
            ):
                boarded = True
                board_call_mileage = (
                    call.mileage + first_call_mileage
                    if call.mileage is not None
                    else None
                )
        if boarded:
            arr_call = TrainLegCallCallInData(
                service.service_uid,
                service.run_date,
                call.plan_arr,
                call.act_arr,
                call.plan_dep,
                call.act_dep,
            )
        else:
            arr_call = None
        for call_association in call.associated_services:
            if call_association.association not in [
                AssociationType.OTHER_DIVIDES,
                AssociationType.THIS_JOINS,
            ]:
                continue
            associated_service = call_association.service
            if associated_service.calls[0].plan_dep is None:
                continue
            associated_leg_calls = get_leg_calls_between_calls(
                associated_service,
                associated_service.calls[0].station_crs,
                associated_service.calls[0].plan_dep,
                end_station_crs,
                board_call_mileage
                if board_call_mileage is not None
                else Decimal(0),
            )
            if associated_leg_calls is None:
                continue
            if boarded:
                associated_leg_calls[0].arr_call = arr_call
                associated_leg_calls[
                    0
                ].associated_type_id = int_of_association_type(
                    call_association.association
                )
            leg_calls.extend(associated_leg_calls)
            return leg_calls
        if boarded:
            leg_call = TrainLegCallInData(
                call.station_crs,
                call.station_name,
                arr_call,
                arr_call,
                (
                    call.mileage - board_call_mileage
                    if call.mileage is not None
                    and board_call_mileage is not None
                    else None
                ),
                None,
            )
            leg_calls.append(leg_call)
            if call.station_crs == end_station_crs:
                return leg_calls
    return None


def get_multiple_short_station_string(
    locs: list[TrainStationIdentifiers],
) -> str:
    string = ""
    for i, loc in enumerate(locs):
        if i == 0:
            string = loc.name
        else:
            string = f"{string} and {loc.name}"
    return string


def short_string_of_service_at_station(service: RttStationService) -> str:
    return f"{service.headcode} {get_multiple_short_station_string(service.origins)} to {get_multiple_short_station_string(service.destinations)}"


def string_of_service_at_station(service: RttStationService) -> str:
    return f"{service.headcode} {get_multiple_short_station_string(service.origins)} to {get_multiple_short_station_string(service.destinations)} plan {get_hourmin_string(service.plan_dep)} act {get_hourmin_string(service.act_dep)} ({service.operator_code})"


def filter_services_by_time_and_stop(
    earliest: datetime,
    latest: datetime,
    origin: TrainStationOutData,
    destination: TrainStationOutData,
    services: list[RttStationService],
) -> list[RttStationServiceToDestination]:
    services_filtered_by_time = filter_services_by_time(
        earliest, latest, services
    )
    services_filtered_by_destination: list[RttStationServiceToDestination] = []
    max_string_length = 0
    for i, service in enumerate(services_filtered_by_time):
        string = f"Checking service {i}/{len(services_filtered_by_time)}: {short_string_of_service_at_station(service)}"
        if service.plan_dep is None:
            continue
        max_string_length = max(max_string_length, len(string))

        information(string.ljust(max_string_length), end="\r")

        full_service = get_service_from_id(
            conn, service.id, service.run_date, scrape_html=False
        )
        if full_service is None:
            continue
        leg_calls_from_origin_to_destination = get_leg_calls_between_calls(
            full_service,
            origin.station_crs,
            service.plan_dep,
            destination.station_crs,
        )
        if leg_calls_from_origin_to_destination is not None:
            services_filtered_by_destination.append(
                RttStationServiceToDestination(
                    service.id,
                    service.headcode,
                    service.run_date,
                    service.origins,
                    service.destinations,
                    service.plan_dep,
                    service.act_dep,
                    service.operator_code,
                    service.brand_code,
                    leg_calls_from_origin_to_destination,
                )
            )

    information(" " * max_string_length, end="\r")

    return services_filtered_by_destination


def get_service_from_service_id_input(
    conn: Connection,
    run_date: datetime,
) -> Optional[RttService]:
    result = None
    while result is None:
        service_id = input_text("Service id")
        if service_id is None:
            return None
        result = get_service_from_id(
            conn, service_id, run_date, scrape_html=True, query_brand=True
        )
        if result is None:
            print("Invalid service id, try again")
        else:
            return result
    return None


def get_service_from_service_at_station_input(
    conn: Connection,
    service_at_station: RttStationServiceToDestination,
    run_date: datetime,
) -> Optional[RttService]:
    service_id = service_at_station.id
    return get_service_from_id(
        conn, service_id, run_date, scrape_html=True, query_brand=True
    )


def string_of_departure(call: RttServiceCall) -> str:
    dep_time = None
    if call.plan_dep is not None:
        dep_time = call.plan_dep
    else:
        dep_time = call.act_dep
    if dep_time is not None:
        time_string = dep_time.strftime("%H:%M")
    else:
        time_string = ""
    if call.platform is not None:
        platform_string = " - Platform {call.platform}"
    else:
        platform_string = ""

    return f"{time_string}{platform_string}"


def get_train_leg_service_from_rtt_service(
    service: RttService,
) -> TrainLegServiceInData:
    return TrainLegServiceInData(
        service.service_uid,
        service.run_date,
        service.headcode,
        service.operator_id,
        service.brand_id,
        service.power,
    )


def get_train_leg_service_endpoints_from_rtt_service(
    service: RttService,
) -> list[TrainLegServiceEndpointInData]:
    train_leg_service_endpoints: list[TrainLegServiceEndpointInData] = []
    for origin in service.origins:
        train_leg_service_endpoints.append(
            TrainLegServiceEndpointInData(
                service.service_uid, service.run_date, origin, True
            )
        )
    for destination in service.destinations:
        train_leg_service_endpoints.append(
            TrainLegServiceEndpointInData(
                service.service_uid, service.run_date, destination, False
            )
        )
    return train_leg_service_endpoints


def get_train_leg_service_calls_from_rtt_service(
    service: RttService,
) -> list[TrainLegServiceCallInData]:
    return [
        TrainLegServiceCallInData(
            service.service_uid,
            service.run_date,
            call.station_crs,
            call.platform,
            call.plan_arr,
            call.act_arr,
            call.plan_dep,
            call.act_dep,
            call.mileage,
        )
        for call in service.calls
    ]


def get_train_leg_service_associations_from_rtt_service(
    service: RttService,
) -> list[TrainLegAssociatedServiceInData]:
    return [
        TrainLegAssociatedServiceInData(
            service.service_uid,
            service.run_date,
            associated_service.call.station_crs,
            associated_service.call.plan_arr,
            associated_service.call.act_arr,
            associated_service.call.plan_dep,
            associated_service.call.act_dep,
            associated_service.service.service_uid,
            associated_service.service.run_date,
            int_of_association_type(associated_service.association),
        )
        for associated_service in service.associated_services
    ]


def get_all_train_leg_service_in_data_from_root_rtt_service(
    root_service: RttService,
) -> tuple[
    list[TrainLegServiceInData],
    list[TrainLegServiceEndpointInData],
    list[TrainLegServiceCallInData],
    list[TrainLegAssociatedServiceInData],
]:
    train_leg_services = [get_train_leg_service_from_rtt_service(root_service)]
    train_leg_service_endpoints = (
        get_train_leg_service_endpoints_from_rtt_service(root_service)
    )
    train_leg_service_calls = get_train_leg_service_calls_from_rtt_service(
        root_service
    )
    train_leg_service_associations = (
        get_train_leg_service_associations_from_rtt_service(root_service)
    )
    for associated_service in root_service.associated_services:
        train_leg_services.append(
            get_train_leg_service_from_rtt_service(associated_service.service)
        )
        train_leg_service_endpoints.extend(
            get_train_leg_service_endpoints_from_rtt_service(
                associated_service.service
            )
        )
        train_leg_service_calls.extend(
            get_train_leg_service_calls_from_rtt_service(
                associated_service.service
            )
        )
        train_leg_service_associations.extend(
            get_train_leg_service_associations_from_rtt_service(
                associated_service.service
            )
        )
    return (
        train_leg_services,
        train_leg_service_endpoints,
        train_leg_service_calls,
        train_leg_service_associations,
    )


def record_new_leg(
    conn: Connection,
    start: datetime | None = None,
    default_station: TrainStationOutData | None = None,
) -> TrainLegInData | None:
    origin_station = get_station_from_input(conn, "Origin", default_station)
    if origin_station is None:
        return None
    destination_station = get_station_from_input(conn, "Destination")
    if destination_station is None:
        return None
    search_datetime = input_datetime(start)
    service_at_station = get_service_at_station(
        conn, origin_station, search_datetime, destination_station
    )
    if service_at_station is None:
        service = get_service_from_service_id_input(conn, search_datetime)
        if service is None:
            return None
        service_calls_at_origin = get_calls_at_station(
            service, origin_station.station_crs
        )
        if len(service_calls_at_origin) == 0:
            information(
                f"No call at {origin_station.station_name} found on service"
            )
            return None

        if len(service_calls_at_origin) > 1:
            origin_call_result = input_select(
                "Select boarding call",
                service_calls_at_origin,
                string_of_departure,
            )
            match origin_call_result:
                case PickSingle(call):
                    origin_call = call
                case _:
                    return None
        else:
            origin_call = service_calls_at_origin[0]
        if origin_call.plan_dep is None:
            return None
        leg_plan_dep = origin_call.plan_dep
    else:
        if service_at_station.plan_dep is None:
            return None
        service = get_service_from_service_at_station_input(
            conn, service_at_station, search_datetime
        )
        if service is None:
            return None
        leg_plan_dep = service_at_station.plan_dep
    leg_calls = get_leg_calls_between_calls(
        service,
        origin_station.station_crs,
        leg_plan_dep,
        destination_station.station_crs,
    )
    if leg_calls is None:
        information(
            f"Could not find route between {origin_station.station_name} and {destination_station.station_crs}"
        )
        return None
    stock_segments = get_stock(conn, leg_calls, service)
    mileage = get_mileage(leg_calls)
    information(f"Computed mileage as {string_of_miles_and_chains(mileage)}")
    (
        train_leg_services,
        train_leg_service_endpoints,
        train_leg_service_calls,
        train_leg_service_associations,
    ) = get_all_train_leg_service_in_data_from_root_rtt_service(service)
    leg = TrainLegInData(
        train_leg_services,
        train_leg_service_endpoints,
        train_leg_service_calls,
        train_leg_service_associations,
        leg_calls,
        stock_segments,
        mileage,
    )
    return leg


def add_to_logfile(conn: Connection) -> None:
    users = input_users(conn)
    if len(users) == 0:
        return None
    leg = record_new_leg(conn)
    if leg is None:
        print("Could not get leg")
        exit(1)
    leg_id = insert_train_leg_fetchone(
        conn, [user.user_id for user in users], leg
    )
    if leg_id is None:
        information(f"Could not insert leg")
    else:
        information(f"Inserted leg id {leg_id}")


def read_logfile(log_file: str) -> dict[str, Any]:
    log: dict[str, Any] = {}
    try:
        with open(log_file, "r") as input:
            log_content = json.load(input)
        if log_content is not None:
            log = log_content
    except:
        debug_msg(f"Logfile {log_file} not found, making empty log")
    return log


def write_logfile(log: dict[str, Any], log_file: str) -> None:
    with open(log_file, "w+") as output:
        json.dump(log, output)


def int_factory(x: Any) -> list[int]:
    return [int(a) for a in x]


if __name__ == "__main__":
    with connect_with_env() as conn:
        register_types(conn)
        add_to_logfile(conn)

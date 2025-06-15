import decimal
import json

from decimal import Decimal
from enum import Enum
from datetime import datetime, timedelta
from typing import Any, Optional, Tuple

from api.classes.train.association import AssociationType
from api.classes.train.leg import (
    TrainLegCallCallInData,
    TrainLegCallInData,
    TrainLegInData,
    TrainStockReportInData,
)
from api.classes.train.service import TrainServiceInData
from api.classes.train.stock import StockReport
from api.db.train.classes.output import (
    string_of_stock_report,
)
from api.db.train.leg import insert_train_leg
from api.pull.train.json import get_service_from_id
from psycopg import Connection

from api.user import input_user
from api.utils.mileage import (
    miles_and_chains_to_miles,
    string_of_miles_and_chains,
)
from api.db.train.toc import get_operator_brands

from api.db.train.stations import (
    TrainServiceAtStation,
    TrainServiceAtStationToDestination,
    TrainStation,
    get_services_at_station,
    select_station_from_crs,
    get_stations_from_substring,
    short_string_of_service_at_station,
    string_of_service_at_station_to_destination,
)
from api.db.train.stock import (
    Class,
    ClassAndSubclass,
    Formation,
    Stock,
    get_operator_stock,
    get_unique_classes,
    get_unique_subclasses,
    select_stock_cars,
    sort_by_classes,
    sort_by_subclasses,
    string_of_class,
    string_of_class_and_subclass,
    string_of_formation,
)
from api.utils.database import connect, get_db_connection_data_from_args
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
from api.utils.times import (
    make_timezone_aware,
    pad_front,
    add,
)
from api.utils.debug import debug_msg


def timedelta_from_string(string: str) -> timedelta:
    parts = string.split(":")
    hour = int(parts[0])
    minutes = int(parts[1])
    return timedelta(hours=hour, minutes=minutes)


def get_input_no(
    prompt: str,
    lower: Optional[int] = None,
    upper: Optional[int] = None,
    default: Optional[int] = None,
    pad: int = 0,
    unknown: bool = False,
) -> Optional[int]:
    """
    Get a natural number of a given length from the user,
    optionally with an upper bound and a default value to use if no input is given
    """
    while True:
        prompt_string = prompt
        # Tell the user the default option
        if default is not None:
            prompt_string = prompt_string + " (" + pad_front(default, pad) + ")"
        prompt_string = prompt_string + ": "
        # Get input from the user
        string = input(prompt_string)
        # If the user gives an empty input, use the default if it exists
        if string == "":
            if default is not None:
                return int(default)
            elif unknown:
                return None
        if not string.isdigit():
            print(f"Expected number but got '{string}'")
        else:
            nat = int(string)
            # Check the number is in the range
            if (
                nat >= 0
                and (upper is None or nat <= upper)
                and (lower is None or nat >= lower)
            ):
                return nat
            else:
                error_msg = "Expected number in range "
                if lower is None:
                    lower_string = "0"
                else:
                    lower_string = str(lower)
                error_msg = f"{error_msg}{lower_string}-"
                if upper is not None:
                    error_msg = f"{error_msg}{upper}"
                error_msg = error_msg + " but got " + string
                print(error_msg)


def get_input_price(prompt: str) -> Decimal:
    while True:
        string = input(f"{prompt} ")
        try:
            price_text = string.replace("£", "")
            price = Decimal(price_text)
            if price < 0:
                print(f"Expected positive price but got '{price}'")
            else:
                return price
        except decimal.InvalidOperation:
            print(f"Expected price but got '{string}'")


def get_station_from_input(
    conn: Connection, prompt: str, stn: TrainStation | None = None
) -> Optional[TrainStation]:
    """
    Get a string specifying a station from a user.
    Can either be a three letter code (in which case confirmation will be asked for)
    or a full station name
    """
    if stn is not None:
        full_prompt = f"{prompt} ({stn.name})"
        default = stn.crs
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
            crs_station = select_station_from_crs(conn, input_string)
            if crs_station is not None:
                resp = input_confirm(f"Did you mean {crs_station.name}")
                if resp:
                    return crs_station
        # Otherwise search for substrings in the full names of stations
        matches = get_stations_from_substring(conn, input_string)
        if len(matches) == 0:
            print("No matches found, try again")
        elif len(matches) == 1:
            match = matches[0]
            resp = input_confirm(f"Did you mean {match.name}?")
            if resp:
                return match
        else:
            print("Multiple matches found: ")
            choice = input_select_paginate(
                "Select a station",
                matches,
                display=lambda x: x.name,
            )
            match choice:
                case PickSingle(stn):
                    return stn
                case _:
                    return None


def get_service_at_station(
    conn: Connection,
    origin: TrainStation,
    search_datetime: datetime,
    destination: TrainStation,
) -> Optional[TrainServiceAtStationToDestination]:
    """
    Record a new journey in the logfile
    """
    origin_services = get_services_at_station(conn, origin, search_datetime)
    # We want to search within a smaller timeframe
    timeframe = 15
    earliest_time = add(search_datetime, -timeframe)
    latest_time = add(search_datetime, timeframe)
    information("Searching for services from " + origin.name)
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
    operator_stock: list[Stock],
) -> Optional[PickUnknown | PickSingle[Class]]:
    valid_classes = get_unique_classes(operator_stock)
    chosen_class = input_select(
        "Class number",
        sort_by_classes(valid_classes),
        unknown=True,
        display=string_of_class,
    )
    match chosen_class:
        case None:
            return None
        case PickUnknown():
            return chosen_class
        case PickSingle(choice):
            return chosen_class
        case _:
            return None


def get_unit_subclass(
    operator_stock: list[Stock], stock_class: Class
) -> Optional[PickUnknown | PickSingle[ClassAndSubclass]]:
    valid_subclasses = get_unique_subclasses(
        operator_stock, stock_class=stock_class
    )
    # If there are no subclasses then we are done
    if len(valid_subclasses) == 0:
        stock_subclass = None
        subclass = ClassAndSubclass(
            stock_class.class_no, stock_class.class_name, None, None
        )
        return PickSingle(subclass)
    elif len(valid_subclasses) == 1:
        stock_subclass = valid_subclasses[0]
        subclass = stock_subclass
        return PickSingle(subclass)
    else:
        chosen_subclass = input_select(
            "Subclass no",
            sort_by_subclasses(valid_subclasses),
            unknown=True,
            cancel=False,
            display=string_of_class_and_subclass,
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


def get_unit_no(stock_subclass: ClassAndSubclass) -> Optional[int]:
    while True:
        unit_no_opt = input_number(
            "Stock number",
            lower=stock_subclass.class_no * 1000,
            upper=stock_subclass.class_no * 1000 + 999,
            unknown=True,
        )
        return unit_no_opt


def get_unit_cars(
    conn: Connection,
    run_date: datetime,
    stock_subclass: ClassAndSubclass,
    operator: str,
    brand: Optional[str],
) -> PickUnknown | PickSingle[Formation] | None:
    stock = Stock(
        stock_subclass.class_no,
        stock_subclass.class_name,
        stock_subclass.subclass_no,
        stock_subclass.subclass_name,
        operator,
        brand,
    )
    car_options = select_stock_cars(conn, stock, run_date)
    # If there is no choice we know the answer already
    if len(car_options) == 1:
        information(
            f"{string_of_class_and_subclass(stock_subclass, name=False)} always has {car_options[0].cars} cars"
        )
        return PickSingle(car_options[0])
    result = input_select(
        "Number of cars", car_options, string_of_formation, unknown=True
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
    conn: Connection,
    run_date: datetime,
    stock_list: list[Stock],
    operator: str,
    brand: Optional[str],
) -> Optional[StockReport]:
    stock_class_res = get_unit_class(stock_list)
    match stock_class_res:
        case None:
            return None
        case PickUnknown():
            stock_class = None
            stock_class_no = None
            stock_subclass = None
            stock_subclass_no = None
            stock_cars = None
            stock_unit_no = None
        case PickSingle(stock_class):
            stock_class_no = stock_class.class_no
            stock_subclass_res = get_unit_subclass(stock_list, stock_class)
            match stock_subclass_res:
                case None:
                    return None
                case PickUnknown():
                    stock_subclass = None
                case PickSingle(choice):
                    stock_subclass = choice
    if stock_class is not None and stock_subclass is None:
        stock_subclass_no = None
        stock_unit_no = None
        stock_cars_res = get_unit_cars(
            conn,
            run_date,
            ClassAndSubclass(
                stock_class.class_no, stock_class.class_name, None, None
            ),
            operator,
            brand,
        )
        match stock_cars_res:
            case None:
                return None
            case PickUnknown():
                stock_cars = None
            case PickSingle(form):
                stock_cars = form
    elif stock_class is not None and stock_subclass is not None:
        stock_subclass_no = stock_subclass.subclass_no
        stock_unit_no = get_unit_no(stock_subclass)
        stock_cars_res = get_unit_cars(
            conn, run_date, stock_subclass, operator, brand
        )
        match stock_cars_res:
            case None:
                return None
            case PickUnknown():
                stock_cars = None
            case PickSingle(form):
                stock_cars = form
    else:
        return None
    return StockReport(
        stock_class_no,
        stock_subclass_no,
        stock_unit_no,
        stock_cars.cars if stock_cars is not None else None,
    )


def get_stock_change_reason() -> StockChange:
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


def get_stock(
    conn: Connection,
    calls: list[TrainLegCallInData],
    service: TrainServiceInData,
    previous: Optional[TrainStockReportInData] = None,
    stock_number: int = 0,
) -> Optional[list[TrainStockReportInData]]:
    information("Recording stock formations")
    used_stock: list[TrainStockReportInData] = []
    last_used_stock = previous

    # Currently getting this automatically isn't implemented
    stock_list = get_operator_stock(
        conn, service.operator_code, service.run_date
    )
    current_call = calls[0]
    remaining_calls = calls[1:]

    while len(remaining_calls) > 0:
        information(
            f"Recording stock formation after {current_call.station_name}"
        )
        segment_stock: list[StockReport] = []
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

        if last_used_stock is None:
            stock_change = StockChange.GAIN
            previous_stock = []
        else:
            stock_change = get_stock_change_reason()
            previous_stock = last_used_stock.stock_report
        match stock_change:
            case StockChange.GAIN:
                segment_stock = previous_stock
                number_of_units = input_number("Number of new units")
                if number_of_units is None:
                    return None
                for i in range(0, number_of_units):
                    information(f"Selecting unit {i+1}")
                    stock_report = get_unit_report(
                        conn,
                        service.run_date,
                        stock_list,
                        service.operator_code,
                        service.brand_code,
                    )
                    if stock_report is None:
                        return None
                    segment_stock.append(stock_report)
            case StockChange.LOSE:
                result = input_checkbox(
                    "Which units remain",
                    previous_stock,
                    string_of_stock_report,
                )
                match result:
                    case None:
                        return None
                    case PickMultiple(choices):
                        segment_stock = choices
        stock_mileage = compute_mileage(stock_calls)
        segment = TrainStockReportInData(
            segment_stock, stock_calls[0], stock_calls[-1], stock_mileage
        )
        used_stock.append(segment)
        last_used_stock = segment
        information(
            f"Stock formation {len(used_stock) + stock_number} recorded"
        )
        current_call = segment_end
    return used_stock


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


def compute_mileage(calls: list[TrainLegCallInData]) -> Decimal:
    start_mileage = calls[0].mileage
    end_mileage = calls[-1].mileage
    if start_mileage is None or end_mileage is None:
        return input_mileage(calls)
    return end_mileage - start_mileage


def filter_services_by_time(
    earliest: datetime, latest: datetime, services: list[TrainServiceAtStation]
) -> list[TrainServiceAtStation]:
    filtered_services: list[TrainServiceAtStation] = []
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


def get_leg_calls_between_calls(
    service: TrainServiceInData,
    start_station_crs: str,
    start_dep_time: datetime,
    end_station_crs: str,
    mileage_offset: Optional[Decimal] = None,
) -> Optional[list[TrainLegCallInData]]:
    start_dep_time = make_timezone_aware(start_dep_time)
    leg_calls: list[TrainLegCallInData] = []
    boarded = False
    mileage_offset = Decimal(0)
    for call in service.calls:
        mileage_offset = (
            (mileage_offset + call.mileage)
            if mileage_offset is not None and call.mileage is not None
            else None
        )
        if (
            not boarded
            and call.station_crs == start_station_crs
            and call.plan_dep == start_dep_time
        ):
            boarded = True
        if boarded:
            arr_call = TrainLegCallCallInData(
                service.unique_identifier,
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
            associated_service = call_association.associated_service
            if associated_service.calls[0].plan_dep is None:
                continue
            associated_leg_calls = get_leg_calls_between_calls(
                associated_service,
                associated_service.calls[0].station_crs,
                associated_service.calls[0].plan_dep,
                end_station_crs,
                mileage_offset,
            )
            if associated_leg_calls is None:
                continue
            if boarded:
                associated_leg_calls[0].arr_call = arr_call
                associated_leg_calls[0].association_type = (
                    call_association.association
                )
            leg_calls.extend(associated_leg_calls)
            return leg_calls
        if boarded:
            leg_call = TrainLegCallInData(
                service,
                call.station_crs,
                call.station_name,
                arr_call,
                arr_call,
                (
                    call.mileage - mileage_offset
                    if call.mileage is not None and mileage_offset is not None
                    else None
                ),
                None,
            )
            leg_calls.append(leg_call)
            if call.station_crs == end_station_crs:
                return leg_calls
    return None


def filter_services_by_time_and_stop(
    earliest: datetime,
    latest: datetime,
    origin: TrainStation,
    destination: TrainStation,
    services: list[TrainServiceAtStation],
) -> list[TrainServiceAtStationToDestination]:
    services_filtered_by_time = filter_services_by_time(
        earliest, latest, services
    )
    services_filtered_by_destination: list[
        TrainServiceAtStationToDestination
    ] = []
    max_string_length = 0
    for i, service in enumerate(services_filtered_by_time):
        string = f"Checking service {i}/{len(services_filtered_by_time)}: {short_string_of_service_at_station(service)}"
        if service.plan_dep is None:
            continue
        max_string_length = max(max_string_length, len(string))

        information(string.ljust(max_string_length), end="\r")

        full_service = get_service_from_id(
            service.id, service.run_date, scrape_html=False
        )
        if full_service is None:
            continue
        leg_calls_from_origin_to_destination = get_leg_calls_between_calls(
            full_service, origin.crs, service.plan_dep, destination.crs
        )
        if leg_calls_from_origin_to_destination is not None:
            services_filtered_by_destination.append(
                TrainServiceAtStationToDestination(
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


def record_new_leg(
    conn: Connection,
    start: datetime | None = None,
    default_station: TrainStation | None = None,
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
    service = None
    service_id = None
    run_date = datetime(
        search_datetime.year, search_datetime.month, search_datetime.day
    )
    if service_at_station is None:
        result = None
        while result is None:
            service_id = input_text("Service id")
            if service_id is None:
                return None
            result = get_service_from_id(service_id, run_date, scrape_html=True)
            if result is None:
                print("Invalid service id, try again")
            else:
                service = result
    else:
        service_id = service_at_station.id
        service = get_service_from_id(service_id, run_date, scrape_html=True)
    if service is None or service_id is None:
        return None
    brands = get_operator_brands(conn, service.operator_code, run_date)
    if len(brands) == 0:
        brand_code = None
    elif len(brands) == 1:
        brand_code = brands[0].code
    else:
        match input_select(
            "Select brand", brands, lambda b: f"{b.name} ({b.code})"
        ):
            case PickSingle(brand):
                brand_code = brand.code
            case _:
                return None
    service.brand_code = brand_code
    for associated_service in service.associated_services:
        associated_service.associated_service.brand_code = brand_code
    stock_segments: list[TrainStockReportInData] = []
    leg_calls: list[TrainLegCallInData] = []
    mileage = compute_mileage(leg_calls)
    information(f"Computed mileage as {string_of_miles_and_chains(mileage)}")
    leg = TrainLegInData(service, leg_calls, mileage, stock_segments)
    return leg


def add_to_logfile(conn: Connection) -> None:
    users = input_user(conn)
    if users is None:
        return None
    leg = record_new_leg(conn)
    if leg is None:
        print("Could not get leg")
        exit(1)
    for user in users:
        insert_train_leg(conn, user, leg)


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


if __name__ == "__main__":
    connection_data = get_db_connection_data_from_args()
    with connect(connection_data) as conn:
        add_to_logfile(conn)

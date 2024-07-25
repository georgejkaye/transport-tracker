from dataclasses import dataclass
from decimal import Decimal
import decimal
import json
from datetime import datetime, timedelta
from typing import Optional
from psycopg2._psycopg import connection, cursor

from train_tracker.data.leg import Leg, StockReport, insert_leg
from train_tracker.data.network import (
    miles_and_chains_to_miles,
    string_of_miles_and_chains,
)
from train_tracker.data.services import (
    TrainService,
    filter_services_by_time_and_stop,
    get_distance_between_stations,
    get_service_from_id,
)
from train_tracker.data.stations import (
    TrainServiceAtStation,
    TrainStation,
    get_services_at_station,
    get_station_from_crs,
    get_stations_from_substring,
    string_of_service_at_station,
)
from train_tracker.data.stock import (
    Class,
    ClassAndSubclass,
    get_operator_stock,
    get_unique_classes,
    get_unique_subclasses,
    sort_by_classes,
    sort_by_subclasses,
    string_of_class,
    string_of_class_and_subclass,
)
from train_tracker.interactive import header, information, option, space, subheader
from train_tracker.times import (
    pad_front,
    add,
)
from train_tracker.debug import debug_msg


def timedelta_from_string(str):
    parts = str.split(":")
    hour = int(parts[0])
    minutes = int(parts[1])
    return timedelta(hours=hour, minutes=minutes)


def get_month_length(month, year):
    """
    Get the length of a month in days, for a given year
    """
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    elif month in [4, 6, 9, 11]:
        return 30
    elif year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        return 29
    else:
        return 28


def get_input_no(
    prompt,
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


def get_input_price(prompt):
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


def yes_or_no(prompt: str):
    """
    Let the user say yes or no
    """
    choice = input(prompt + " (Y/n) ")
    if choice == "y" or choice == "Y" or choice == "":
        return True
    return False


@dataclass
class PickSingle[T]:
    choice: T


@dataclass
class PickMultiple[T]:
    choices: list[T]


@dataclass
class PickUnknown:
    pass


@dataclass
class PickCancel:
    pass


type PickChoice[T] = PickSingle[T] | PickMultiple[T] | PickUnknown | PickCancel


def pick_from_list[
    T
](
    choices: list[T],
    prompt: str,
    cancel: bool = False,
    unknown: bool = False,
    display=lambda x: x,
) -> PickChoice[T]:
    """
    Let the user pick from a list of choices
    """
    for i, choice in enumerate(choices):
        option(i + 1, display(choice))
    max_choice = len(choices)
    if unknown:
        max_choice = max_choice + 1
        unknown_choice = max_choice
        option(max_choice, "Unknown")
    if cancel:
        max_choice = len(choices) + 1
        cancel_choice = max_choice
        # The last option is a cancel option, this returns None
        option(max_choice, "Cancel")
    while True:
        space()
        resp = input(prompt + " (1-" + str(max_choice) + "): ")
        if not resp.isdigit():
            print("Expected number")
        else:
            resp_no = int(resp)
            if cancel and resp_no == cancel_choice:
                return PickCancel()
            elif unknown and resp_no == unknown_choice:
                return PickUnknown()
            elif resp_no > 0 and resp_no <= len(choices):
                return PickSingle(choices[resp_no - 1])
            print(f"Expected number 1-{max_choice} but got '{resp_no}'")


def get_station_from_input(
    cur: cursor, prompt: str, stn: TrainStation | None = None
) -> Optional[TrainStation]:
    """
    Get a string specifying a station from a user.
    Can either be a three letter code (in which case confirmation will be asked for)
    or a full station name
    """
    if stn is not None:
        prompt = f"{prompt} ({stn.name})"
    prompt = f"{prompt}: "
    while True:
        string = input(prompt).lower()
        # We only search for strings of length at least three, otherwise there would be loads
        if len(string) == 0 and stn is not None:
            return stn
        if len(string) == 3:
            crs_station = get_station_from_crs(cur, string)
            if crs_station is not None:
                resp = yes_or_no(f"Did you mean {crs_station.name}")
                if resp:
                    return crs_station
        # Otherwise search for substrings in the full names of stations
        matches = get_stations_from_substring(cur, string)
        if len(matches) == 0:
            print("No matches found, try again")
        elif len(matches) == 1:
            match = matches[0]
            resp = yes_or_no(f"Did you mean {match}?")
            if resp:
                return match
        else:
            print("Multiple matches found: ")
            choice = pick_from_list(
                matches, "Select a station", cancel=True, display=lambda x: x.name
            )
            match choice:
                case PickSingle(stn):
                    return stn
                case _:
                    return None


def get_service_at_station(
    cur: cursor,
    origin: TrainStation,
    dt: datetime,
    destination: TrainStation,
) -> Optional[TrainServiceAtStation]:
    """
    Record a new journey in the logfile
    """
    origin_services = get_services_at_station(cur, origin, dt)
    # We want to search within a smaller timeframe
    timeframe = 15
    earliest_time = add(dt, -timeframe)
    latest_time = add(dt, timeframe)
    debug_msg("Searching for services from " + origin.name)
    # The results encompass a ~1 hour period
    # We only want to check our given timeframe
    # We also only want services that stop at our destination
    filtered_services = filter_services_by_time_and_stop(
        cur, earliest_time, latest_time, origin, destination, origin_services
    )
    choice = pick_from_list(
        filtered_services,
        "Pick a service",
        cancel=True,
        display=lambda x: string_of_service_at_station(x),
    )
    match choice:
        case PickSingle(service):
            return service
        case _:
            return None


def get_stock(cur: cursor, service: TrainService) -> list[StockReport]:
    used_stock = []
    # Currently getting this automatically isn't implemented
    # First get all stock this operator has
    stock_list = get_operator_stock(cur, service.operator_id)
    # Get the unique classes to pick from
    operator_classes = get_unique_classes(stock_list)
    number_of_units = get_input_no("Number of units", default=1)
    if number_of_units is None:
        raise RuntimeError("Could not get number of units")
    for i in range(0, number_of_units):
        header(f"Selecting unit {i+1}")
        subheader("Selecting unit class")
        chosen_class: PickChoice[Class] = pick_from_list(
            sort_by_classes(operator_classes),
            "Class number",
            unknown=True,
            display=string_of_class,
        )
        match chosen_class:
            case PickUnknown():
                used_stock.append(StockReport(None, None, None))
            case PickSingle(choice):
                stock_class = choice
                operator_subclasses = get_unique_subclasses(
                    stock_list, stock_class=stock_class
                )
                # If there are no subclasses then we are done
                if len(operator_subclasses) == 0:
                    stock_subclass = None
                    subheader(f"Class {stock_class.class_no} has no subclass variants")
                elif len(operator_subclasses) == 1:
                    stock_subclass = operator_subclasses[0].subclass_no
                    subheader(
                        f"Class {stock_class.class_no} only has /{stock_subclass} variant for this operator"
                    )
                else:
                    subheader("Selecting unit subclass")
                    chosen_subclass: PickChoice[ClassAndSubclass] = pick_from_list(
                        sort_by_subclasses(operator_subclasses),
                        "Subclass no",
                        unknown=True,
                        cancel=False,
                        display=string_of_class_and_subclass,
                    )
                    match chosen_subclass:
                        case PickUnknown():
                            stock_subclass = None
                        case PickSingle(choice):
                            stock_subclass = choice.subclass_no
                # Stock number input
                minimum_stock_number = stock_class.class_no * 1000
                maximum_stock_number = minimum_stock_number + 999
                if stock_subclass is not None:
                    minimum_stock_number = minimum_stock_number + (stock_subclass * 100)
                    maximum_stock_number = minimum_stock_number + 99
                subheader("Selecting stock number")
                stock_number = get_input_no(
                    "Stock number",
                    lower=minimum_stock_number,
                    upper=maximum_stock_number,
                    unknown=True,
                )
                used_stock.append(
                    StockReport(stock_class.class_no, stock_subclass, stock_number)
                )
    return used_stock


def get_mileage() -> Decimal:
    # If we can get a good distance set this could be automated
    miles = get_input_no("Miles")
    chains = get_input_no("Chains", upper=79)
    if miles is None or chains is None:
        raise RuntimeError("Cannot be None")
    return miles_and_chains_to_miles(miles, chains)


def compute_mileage(service: TrainService, origin: str, destination: str) -> Decimal:
    mileage = get_distance_between_stations(service, origin, destination)
    if mileage is None:
        return get_mileage()
    return mileage


def get_datetime(start: Optional[datetime] = None):
    if start is None:
        start = datetime.now()
    year = get_input_no("Year", upper=2022, default=start.year, pad=4)
    month = get_input_no("Month", upper=12, default=start.month, pad=2)
    max_days = get_month_length(month, year)
    day = get_input_no("Day", upper=max_days, default=start.day, pad=2)
    time = get_input_no(
        "Time", upper=2359, default=start.hour * 100 + start.minute, pad=4
    )
    if year is None or month is None or day is None or time is None:
        raise RuntimeError("Cannot be None")
    time_string = pad_front(time, 4)
    hour = int(time_string[0:2])
    minute = int(time_string[2:4])
    return datetime(year, month, day, hour, minute)


def record_new_leg(
    cur: cursor,
    start: datetime | None = None,
    default_station: TrainStation | None = None,
) -> Leg | None:
    origin_station = get_station_from_input(cur, "Origin", default_station)
    if origin_station is None:
        return None
    destination_station = get_station_from_input(cur, "Destination")
    if destination_station is None:
        return None
    run_date = get_datetime(start)
    service_at_station = get_service_at_station(
        cur, origin_station, run_date, destination_station
    )
    service = None
    if service_at_station is None:
        service_candidate = None
        while service_candidate is None:
            service_id = input("Service id: ")
            service_candidate = get_service_from_id(cur, service_id, run_date)
            if service_candidate is None:
                print("Invalid service id, try again")
            else:
                service = service_candidate
    else:
        service = get_service_from_id(cur, service_at_station.id, run_date)
    if service is None:
        raise RuntimeError("Service should not be none at this point")
    stock = get_stock(cur, service)
    mileage = compute_mileage(service, origin_station.crs, destination_station.crs)
    information(f"Computed mileage as {string_of_miles_and_chains(mileage)}")
    leg = Leg(service, origin_station.crs, destination_station.crs, mileage, stock)
    return leg


def add_to_logfile(conn: connection, cur: cursor):
    leg = record_new_leg(cur)
    if leg is None:
        print("Could not get leg")
        exit(1)
    insert_leg(conn, cur, leg)


def read_logfile(log_file: str):
    log = {}
    try:
        with open(log_file, "r") as input:
            log = json.load(input)
        if log is None:
            log = {}
    except:
        debug_msg(f"Logfile {log_file} not found, making empty log")
    return log


def write_logfile(log, log_file: str):
    with open(log_file, "w+") as output:
        json.dump(log, output)

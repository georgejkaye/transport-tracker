from decimal import Decimal
import decimal
import json
from datetime import date, datetime, timedelta
from typing import Optional
from train_tracker.api import Credentials
from psycopg2._psycopg import connection, cursor

from train_tracker.data.leg import Leg
from train_tracker.data.network import miles_and_chains_to_miles
from train_tracker.data.services import (
    TrainService,
    filter_services_by_time_and_stop,
    get_mileage_for_service_call,
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
from train_tracker.data.stock import get_operator_stock, string_of_stock
from train_tracker.times import (
    get_diff_struct,
    get_duration_string,
    pad_front,
    add,
    get_hourmin_string,
    get_diff_string,
    to_time,
    get_status,
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


def get_input_no(prompt, upper=-1, default=-1, default_pad=0):
    """
    Get a natural number of a given length from the user,
    optionally with an upper bound and a default value to use if no input is given
    """
    while True:
        prompt_string = prompt
        # Tell the user the default option
        if default != -1:
            prompt_string = prompt_string + " (" + pad_front(default, default_pad) + ")"
        prompt_string = prompt_string + ": "
        # Get input from the user
        string = input(prompt_string)
        # If the user gives an empty input, use the default if it exists
        if string == "" and default != -1:
            return int(default)
        try:
            nat = int(string)
            # Check the number is in the range
            if nat >= 0 and (upper == -1 or nat <= upper):
                return nat
            else:
                error_msg = "Expected number in range 0-"
                if upper != -1:
                    error_msg = f"{error_msg}{upper}"
                error_msg = error_msg + " but got " + string
                print(error_msg)
        except:
            print(f"Expected number but got '{string}'")


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
            choice = pick_from_list(matches, "Select a station", True, lambda x: x.name)
            if choice is not None:
                return choice


def yes_or_no(prompt: str):
    """
    Let the user say yes or no
    """
    choice = input(prompt + " (Y/n) ")
    if choice == "y" or choice == "Y" or choice == "":
        return True
    return False


def pick_from_list[T](choices: list[T], prompt: str, cancel: bool, display=lambda x: x):
    """
    Let the user pick from a list of choices
    """
    for i, choice in enumerate(choices):
        print(str(i + 1) + ": " + display(choice))
    if cancel:
        max_choice = len(choices) + 1
        # The last option is a cancel option, this returns None
        print(str(max_choice) + ": Cancel")
    else:
        max_choice = len(choices)
    while True:
        resp = input(prompt + " (1-" + str(max_choice) + "): ")
        try:
            resp_no = int(resp)
            if cancel and resp == len(choices) + 1:
                return None
            elif resp_no > 0 or resp_no < len(choices):
                return choices[resp_no - 1]
            print(f"Expected number 1-{max_choice} but got '{resp_no}'")
        except:
            print(f"Expected number 1-{max_choice} but got '{resp_no}'")


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
    # The results encompass a ~1 hour period
    # We only want to check our given timeframe
    # We also only want services that stop at our destination
    filtered_services = filter_services_by_time_and_stop(
        cur, earliest_time, latest_time, origin, destination, origin_services
    )
    debug_msg("Searching for services from " + origin.name)
    choice = pick_from_list(
        filtered_services,
        "Pick a service",
        True,
        lambda x: string_of_service_at_station(x),
    )
    return choice


def get_stock(cur: cursor, service: TrainService):
    # Currently getting this automatically isn't implemented
    # We could trawl wikipedia and make a map of which trains operate which services
    # Or if know your train becomes part of the api
    stock_list = get_operator_stock(cur, service.operator_id)
    stock = pick_from_list(
        stock_list, "Stock", False, display=lambda s: string_of_stock(s)
    )
    if stock is None:
        print("Could not get stuck")
        exit(1)
    return stock


def compute_mileage(service: TrainService, origin: str, destination: str) -> Decimal:
    origin_mileage = get_mileage_for_service_call(service, origin)
    if origin_mileage is None:
        return get_mileage()
    else:
        destination_mileage = get_mileage_for_service_call(service, destination)
        if destination_mileage is None:
            return get_mileage()
        else:
            return destination_mileage - origin_mileage


def get_mileage() -> Decimal:
    # If we can get a good distance set this could be automated
    miles = get_input_no("Miles")
    chains = get_input_no("Chains", 79)
    return miles_and_chains_to_miles(miles, chains)


def get_datetime(start: Optional[datetime] = None):
    if start is None:
        start = datetime.now()
    year = get_input_no("Year", 2022, start.year, 4)
    month = get_input_no("Month", 12, start.month, 2)
    max_days = get_month_length(month, year)
    day = get_input_no("Day", max_days, start.day, 2)
    time = get_input_no("Time", 2359, start.hour * 100 + start.minute, 4)
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
    leg = Leg(service, origin_station.crs, destination_station.crs, mileage, stock)
    return leg


def add_to_logfile(cur: cursor):
    journey = record_new_leg(cur)


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

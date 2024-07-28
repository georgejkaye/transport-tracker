from decimal import Decimal
import decimal
from enum import Enum
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple
from psycopg2._psycopg import connection, cursor
from train_tracker.data.leg import (
    Leg,
    LegSegmentStock,
    StockReport,
    insert_leg,
    string_of_stock_report,
)
from train_tracker.data.network import (
    miles_and_chains_to_miles,
    string_of_miles_and_chains,
)
from train_tracker.data.services import (
    LegCall,
    TrainService,
    filter_services_by_time_and_stop,
    get_calls,
    get_distance_between_stations,
    get_service_from_id,
)
from train_tracker.data.stations import (
    ShortTrainStation,
    TrainServiceAtStation,
    TrainStation,
    compare_crs,
    get_services_at_station,
    get_station_from_crs,
    get_stations_from_substring,
    string_of_service_at_station,
    string_of_short_train_station,
)
from train_tracker.data.stock import (
    Class,
    ClassAndSubclass,
    Stock,
    get_number,
    get_operator_stock,
    get_unique_classes,
    get_unique_classes_from_subclasses,
    get_unique_subclasses,
    sort_by_classes,
    sort_by_subclasses,
    string_of_class,
    string_of_class_and_subclass,
)
from train_tracker.interactive import (
    PickMultiple,
    PickSingle,
    PickUnknown,
    information,
    input_checkbox,
    input_confirm,
    input_day,
    input_month,
    input_number,
    input_select,
    input_text,
    input_time,
    input_year,
)
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


def get_station_from_input(
    cur: cursor, prompt: str, stn: TrainStation | None = None
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
            crs_station = get_station_from_crs(cur, input_string)
            if crs_station is not None:
                resp = input_confirm(f"Did you mean {crs_station.name}")
                if resp:
                    return crs_station
        # Otherwise search for substrings in the full names of stations
        matches = get_stations_from_substring(cur, input_string)
        if len(matches) == 0:
            print("No matches found, try again")
        elif len(matches) == 1:
            match = matches[0]
            resp = input_confirm(f"Did you mean {match.name}?")
            if resp:
                return match
        else:
            print("Multiple matches found: ")
            choice = input_select(
                "Select a station", matches, display=lambda x: x.name, cancel=True
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
    information("Searching for services from " + origin.name)
    # The results encompass a ~1 hour period
    # We only want to check our given timeframe
    # We also only want services that stop at our destination
    filtered_services = filter_services_by_time_and_stop(
        cur, earliest_time, latest_time, origin, destination, origin_services
    )
    if len(filtered_services) == 0:
        return None
    choice = input_select(
        "Pick a service",
        filtered_services,
        cancel=True,
        display=lambda x: string_of_service_at_station(x),
    )
    match choice:
        case PickSingle(service):
            return service
        case _:
            return None


def get_unit_class(operator_stock: list[Stock]) -> Optional[Class]:
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
            return None
        case PickSingle(choice):
            return choice


def get_unit_subclass(
    operator_stock: list[Stock], stock_class: Class
) -> Optional[ClassAndSubclass]:
    valid_subclasses = get_unique_subclasses(operator_stock, stock_class=stock_class)
    # If there are no subclasses then we are done
    if len(valid_subclasses) == 0:
        stock_subclass = None
        subclass = ClassAndSubclass(
            stock_class.class_no, stock_class.class_name, None, None
        )
    elif len(valid_subclasses) == 1:
        stock_subclass = valid_subclasses[0]
        subclass = stock_subclass
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
                subclass = None
            case PickSingle(choice):
                subclass = choice
    return subclass


def get_unit_no(stock_subclass: ClassAndSubclass) -> Optional[int]:
    while True:
        unit_no_opt = input_number(
            "Stock number",
            lower=stock_subclass.class_no * 1000,
            upper=stock_subclass.class_no * 1000 + 999,
            unknown=True,
        )
        return unit_no_opt


def get_station_from_calls(
    calls: list[LegCall],
) -> Optional[Tuple[ShortTrainStation, list[LegCall]]]:
    end_call = input_select(
        "Stock formation until",
        [(i, call) for (i, call) in enumerate(calls)],
        display=lambda x: string_of_short_train_station(x[1].station),
        unknown=True,
    )
    match end_call:
        case PickSingle((i, call)):
            return (call.station, calls[i + 1 :])
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


def get_unit_report(stock_list: list[Stock]) -> StockReport:
    stock_class = get_unit_class(stock_list)
    if stock_class is None:
        stock_class_no = None
        stock_subclass = None
    else:
        stock_class_no = stock_class.class_no
        stock_subclass = get_unit_subclass(stock_list, stock_class)
    if stock_subclass is None:
        stock_subclass_no = None
        stock_unit_no = None
    else:
        stock_subclass_no = stock_subclass.subclass_no
        stock_unit_no = get_unit_no(stock_subclass)
    return StockReport(stock_class_no, stock_subclass_no, stock_unit_no)


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
    cur: cursor,
    calls: list[LegCall],
    service: TrainService,
) -> list[LegSegmentStock]:
    information("Recording stock formations")
    used_stock: list[LegSegmentStock] = []
    # Currently getting this automatically isn't implemented
    # First get all stock this operator has
    stock_list = get_operator_stock(cur, service.operator_id)
    first_station = calls[0].station
    current_station = first_station
    last_station = calls[-1].station
    # To determine when a particular stock formation lasts
    # we prompt the user to pick where it ends from a list
    # of stops excluding the start
    remaining_calls = calls[1:]
    while not compare_crs(current_station.crs, last_station.crs):
        information(f"Recording stock formation after {current_station.name}")
        segment_stock: list[StockReport] = []
        segment_start = current_station
        # Find out where this stock ends
        # If we don't know, then this will be the last report
        stock_end_opt = get_station_from_calls(remaining_calls)
        if stock_end_opt is None:
            segment_end = last_station
        else:
            (stock_end, remaining_calls) = stock_end_opt
            segment_end = stock_end
        # Now find out what reason for the change in stock is (or if we are just startin)
        if len(used_stock) == 0:
            stock_change = StockChange.GAIN
            previous_stock = []
        else:
            stock_change = get_stock_change_reason()
            previous_stock = used_stock[-1].stock
        match stock_change:
            case StockChange.GAIN:
                segment_stock = [s for s in previous_stock]
                number_of_units = input_number("Number of new units")
                if number_of_units is None:
                    raise RuntimeError("Could not get number of units")
                for i in range(0, number_of_units):
                    information(f"Selecting unit {i+1}")
                    stock_report = get_unit_report(stock_list)
                    segment_stock.append(stock_report)
            case StockChange.LOSE:
                result = input_checkbox(
                    "Which units remain", previous_stock, string_of_stock_report
                )
                match result:
                    case None:
                        raise RuntimeError()
                    case PickMultiple(choices):
                        segment_stock = choices
        used_stock.append(LegSegmentStock(segment_stock, segment_start, segment_end))
        information(f"Stock formation {len(used_stock)} recorded")
        current_station = segment_end
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


def get_datetime(start: Optional[datetime] = None) -> datetime:
    if start is not None:
        default_year = start.year
        default_month = start.month
        default_day = start.day
        default_time = start
    else:
        default_year = None
        default_month = None
        default_day = None
        default_time = None
    year = input_year(default=default_year)
    if year is None:
        raise RuntimeError()
    month = input_month(default=default_month)
    if month is None:
        raise RuntimeError()
    date = input_day(month, year, default=default_day)
    if date is None:
        raise RuntimeError()
    time = input_time(default=default_time)
    if time is None:
        raise RuntimeError()
    return datetime(year, month, date, time.hour, time.minute)


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
            service_id = input_text("Service id")
            if service_id is None:
                return None
            service_candidate = get_service_from_id(cur, service_id, run_date)
            if service_candidate is None:
                print("Invalid service id, try again")
            else:
                service = service_candidate
    else:
        service = get_service_from_id(cur, service_at_station.id, run_date)
    if service is None:
        raise RuntimeError("Service should not be none at this point")
    calls = get_calls(service.calls, origin_station.crs, destination_station.crs)
    if calls is None:
        raise RuntimeError()
    stock = get_stock(cur, calls, service)
    mileage = compute_mileage(service, origin_station.crs, destination_station.crs)
    information(f"Computed mileage as {string_of_miles_and_chains(mileage)}")
    leg = Leg(service, calls, mileage, stock)
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

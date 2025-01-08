import decimal
import json
import psycopg

from decimal import Decimal
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Tuple
from psycopg import Cursor, Connection

from api.data.leg import (
    Leg,
    LegSegmentStock,
    StockReport,
    insert_leg,
    string_of_enumerated_stock_report,
)
from api.data.mileage import (
    miles_and_chains_to_miles,
    string_of_miles_and_chains,
)
from api.data.services import (
    LegCall,
    TrainServiceRaw,
    filter_services_by_time_and_stop,
    get_calls_between_stations,
    get_service_from_id,
)
from api.data.stations import (
    TrainServiceAtStation,
    TrainStation,
    compare_crs,
    get_services_at_station,
    select_station_from_crs,
    get_stations_from_substring,
    string_of_service_at_station,
    string_of_short_train_station,
)
from api.data.stock import (
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
from api.interactive import (
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
from api.times import (
    pad_front,
    add,
)
from api.debug import debug_msg


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
    cur: Cursor, prompt: str, stn: TrainStation | None = None
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
            crs_station = select_station_from_crs(cur, input_string)
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
                "Select a station",
                matches,
                display=lambda x: x.name,
                cancel=True,
            )
            match choice:
                case PickSingle(stn):
                    return stn
                case _:
                    return None


def get_service_at_station(
    cur: Cursor,
    origin: TrainStation,
    search_datetime: datetime,
    destination: TrainStation,
) -> Optional[TrainServiceAtStation]:
    """
    Record a new journey in the logfile
    """
    origin_services = get_services_at_station(cur, origin, search_datetime)
    # We want to search within a smaller timeframe
    timeframe = 15
    earliest_time = add(search_datetime, -timeframe)
    latest_time = add(search_datetime, timeframe)
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
    cur: Cursor,
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
    car_options = select_stock_cars(cur, stock, run_date)
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


def get_station_from_calls(
    current: LegCall,
    calls: list[LegCall],
) -> Optional[Tuple[LegCall, int, list[LegCall]]]:
    end_call = input_select(
        f"Stock formation from {current.station.name} until",
        [(i, call) for (i, call) in enumerate(calls)],
        display=lambda x: string_of_short_train_station(x[1].station),
        unknown=True,
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
    cur: Cursor,
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
            cur,
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
            cur, run_date, stock_subclass, operator, brand
        )
        match stock_cars_res:
            case None:
                return None
            case PickUnknown():
                stock_cars = None
            case PickSingle(form):
                stock_cars = form
    return StockReport(
        stock_class_no, stock_subclass_no, stock_unit_no, stock_cars
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
    cur: Cursor,
    calls: list[LegCall],
    service: TrainServiceRaw,
    previous: Optional[LegSegmentStock] = None,
    stock_number: int = 0,
) -> Optional[list[LegSegmentStock]]:
    information("Recording stock formations")
    used_stock: list[LegSegmentStock] = []
    last_used_stock = previous
    # Currently getting this automatically isn't implemented
    # First get all stock this operator has
    stock_list = get_operator_stock(
        cur, service.operator_code, service.run_date
    )
    first_call = calls[0]
    current_call = first_call
    last_call = calls[-1]
    # To determine when a particular stock formation lasts
    # we prompt the user to pick where it ends from a list
    # of stops excluding the start
    remaining_calls = calls[1:]
    while not compare_crs(current_call.station.crs, last_call.station.crs):
        information(
            f"Recording stock formation after {current_call.station.name}"
        )
        segment_stock: list[StockReport] = []
        segment_start = current_call
        # Find out where this stock ends
        # If we don't know, then this will be the last report
        stock_end_opt = get_station_from_calls(segment_start, remaining_calls)
        if stock_end_opt is None:
            segment_end = last_call
            segment_end_index = len(calls) - 1
            next_remaining_calls = []
        else:
            (stock_end, segment_end_index, next_remaining_calls) = stock_end_opt
        stock_calls = [current_call] + remaining_calls[
            0 : segment_end_index + 1
        ]
        remaining_calls = next_remaining_calls
        segment_end = stock_calls[-1]
        # Now find out what reason for the change in stock is (or if we are just startin)
        if last_used_stock is None:
            stock_change = StockChange.GAIN
            previous_stock = []
        else:
            stock_change = get_stock_change_reason()
            previous_stock = [
                (i, stock) for (i, stock) in enumerate(last_used_stock.stock)
            ]
        match stock_change:
            case StockChange.GAIN:
                segment_stock = [s for (i, s) in previous_stock]
                number_of_units = input_number("Number of new units")
                if number_of_units is None:
                    return None
                for i in range(0, number_of_units):
                    information(f"Selecting unit {i+1}")
                    stock_report = get_unit_report(
                        cur,
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
                    string_of_enumerated_stock_report,
                )
                match result:
                    case None:
                        return None
                    case PickMultiple(choices):
                        segment_stock = [s for (i, s) in choices]
        stock_mileage = compute_mileage(stock_calls)
        segment = LegSegmentStock(segment_stock, stock_calls, stock_mileage)
        used_stock.append(segment)
        last_used_stock = segment
        information(
            f"Stock formation {len(used_stock) + stock_number} recorded"
        )
        current_call = segment_end
    return used_stock


def get_mileage(calls: list[LegCall]) -> Decimal:
    information(
        f"Manual mileage input between {calls[0].station.name} and {calls[-1].station.name} required"
    )
    # If we can get a good distance set this could be automated
    miles = input_number("Miles")
    chains = input_number("Chains", upper=79)
    if miles is None or chains is None:
        raise RuntimeError("Cannot be None")
    return miles_and_chains_to_miles(miles, chains)


def compute_mileage(calls: list[LegCall]) -> Decimal:
    start_mileage = calls[0].mileage
    end_mileage = calls[-1].mileage
    if start_mileage is None or end_mileage is None:
        return get_mileage(calls)
    return end_mileage - start_mileage


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
    cur: Cursor,
    start: datetime | None = None,
    default_station: TrainStation | None = None,
) -> Leg | None:
    origin_station = get_station_from_input(cur, "Origin", default_station)
    if origin_station is None:
        return None
    destination_station = get_station_from_input(cur, "Destination")
    if destination_station is None:
        return None
    search_datetime = get_datetime(start)
    service_at_station = get_service_at_station(
        cur, origin_station, search_datetime, destination_station
    )
    service = None
    run_date = datetime(
        search_datetime.year, search_datetime.month, search_datetime.day
    )
    if service_at_station is None:
        service_candidate = None
        while service_candidate is None:
            service_id = input_text("Service id")
            if service_id is None:
                return None
            service_candidate = get_service_from_id(
                cur, service_id, run_date, soup=True
            )
            if service_candidate is None:
                print("Invalid service id, try again")
            else:
                service = service_candidate
    else:
        service = get_service_from_id(
            cur, service_at_station.id, run_date, soup=True
        )
    if service is None:
        return None
    calls = get_calls_between_stations(
        service, service.calls, origin_station.crs, destination_station.crs
    )
    if calls is None:
        return None
    call_chain, service_chains = calls
    stock_segments = []
    for chain in service_chains:
        if len(stock_segments) > 0:
            previous = stock_segments[-1]
        else:
            previous = None
        chain_stock = get_stock(
            cur, chain, service, previous, len(stock_segments)
        )
        if chain_stock is None:
            return None
        stock_segments.extend(chain_stock)
    mileage = compute_mileage(call_chain)
    information(f"Computed mileage as {string_of_miles_and_chains(mileage)}")
    leg = Leg(service, call_chain, mileage, stock_segments)
    return leg


def add_to_logfile(conn: Connection, cur: Cursor):
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

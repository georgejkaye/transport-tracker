import yaml
from datetime import date, time, datetime
from pathlib import Path


from api import filter_services_by_stop, filter_services_by_time, get_destinations_full, get_headcode_full, get_locs_full, get_operator_code_full, get_operator_full, get_origins_full, get_services, get_station_name, get_uid_full, request_station_at_time, service_to_string_full, service_to_string_full_from_station, short_service_string
from network import get_matching_station_names, station_codes, station_names, station_code_to_name, station_name_to_code, stock_dict
from time import add, get_hourmin_string, get_diff_string, get_duration
from structures import Mileage, PlanActTime, Service, ShortLocation, Station, Location, get_mph_string
from debug import debug


def pad_front(string, length):
    """
    Add zeroes to the front of a number string until it is the desired length
    """
    string = str(string)
    return "0" * (length - len(string)) + string


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


def get_input_no(length, prompt, upper=-1, default=-1):
    """
    Get a natural number of a given length from the user,
    optionally with an upper bound and a default value to use if no input is given
    """
    while True:
        prompt_string = prompt
        # Tell the user the default option
        if default != -1:
            prompt_string = prompt_string + " (" + str(default) + ")"
        prompt_string = prompt_string + ": "
        # Get input from the user
        string = input(prompt_string)
        # If the user gives an empty input, use the default if it exists
        if string == "" and default != -1:
            return default
        try:
            nat = int(string)
            # Check the number is in the range
            if nat > 0 and (upper == -1 or nat <= upper):
                if len(string) < length:
                    if length != -1:
                        string = pad_front(string, length)
                return string
            else:
                error_msg = "Expected number in range 0-"
                if upper != -1:
                    error_msg = error_msg + upper
                error_msg = error_msg + " but got " + string
                print(error_msg)
        except:
            print("Expected number but got '" + string + "'")


def get_station_string(prompt: str):
    """
    Get a string specifying a station from a user.
    Can either be a three letter code (in which case confirmation will be asked for)
    or a full station name
    """
    while True:
        string = input(prompt + ": ").upper()
        # We only search for strings of length at least three, otherwise there would be loads
        if len(string) >= 3:
            # Check the three letter codes first
            if string in station_codes:
                name = station_code_to_name[string]
                # Just check that it's right, often the tlc is a guess
                resp = yes_or_no("Did you mean " + name + "?")
                if resp:
                    return name
            # Otherwise search for substrings in the full names of stations
            matches = get_matching_station_names(string.lower().strip())
            if len(matches) == 0:
                print("No matches found, try again")
            elif len(matches) == 1:
                return station_name_to_code[matches[0]]
            print("Multiple matches found: ")
            choice = pick_from_list(matches, "Select a station")
            if choice != "":
                return station_name_to_code[choice]
        else:
            print("Search string must be at least three characters")


def yes_or_no(prompt: str):
    """
    Let the user say yes or no
    """
    choice = input(prompt + " (Y/n)")
    if choice == "y" or choice == "Y" or choice == "":
        return True
    return False


def pick_from_list(choices: list, prompt: str, display=lambda x: x):
    """
    Let the user pick from a list of choices
    """
    for i, choice in enumerate(choices):
        print(str(i+1) + ": " + display(choice))
    max_choice = len(choices) + 1
    # The last option is a cancel option, this returns None
    print(str(max_choice) + ": Cancel")
    while True:
        resp = input(prompt + " (1-" + str(max_choice) + "): ")
        try:
            resp = int(resp)
            if resp == len(choices) + 1:
                return None
            elif resp > 0 or resp < len(choices):
                return choices[resp-1]
            print(f'Expected number 1-{max_choice} but got \'{resp}\'')
        except:
            print(f'Expected number 1-{max_choice} but got \'{resp}\'')


def get_service(station: Station, destination_crs: str):
    """
    Record a new journey in the logfile
    """

    while True:
        services = station.services

        if services is not None:
            # We want to search within a smaller timeframe
            timeframe = 15

            earliest_time = add(station.datetime, timeframe)
            latest_time = add(station.datetime, -timeframe)
            # The results encompass a ~1 hour period
            # We only want to check our given timeframe
            # We also only want services that stop at our destination
            filtered_services = station.filter_services_by_time_and_stop(
                earliest_time, latest_time, station.crs, destination_crs
            )

            debug("Searching for services from " + station.name)
            choice = pick_from_list(
                filtered_services, "Pick a service", lambda x: x.get_string())

            if choice is not None:
                return choice
        else:
            print("No services found!")


def get_stock(service: Service):
    # Currently getting this automatically isn't implemented
    # We could trawl wikipedia and make a map of which trains operate which services
    # Or if know your train becomes part of the api
    stock = pick_from_list(stock_dict[service.toc], "Stock")
    return stock


def get_mileage():
    # If we can get a good distance set this could be automated
    miles = get_input_no(-1, "Miles")
    chains = get_input_no(2, "Chains", 79)
    return Mileage(miles, chains)


def make_short_loc_entry(loc: ShortLocation, origin: bool):
    entry = {
        "name": loc.name,
        "crs": loc.crs
    }
    time_string = get_hourmin_string(loc.time)
    if origin:
        entry["dep_plan"] = time_string
    else:
        entry["arr_plan"] = time_string
    return entry


def make_planact_entry(planact: PlanActTime):
    entry = {
        "plan": planact.plan
    }
    if planact.act is not None:
        entry["act"] = planact.act
        entry["diff"] = get_diff_string(planact.diff)
        entry["status"] = planact.status


def make_loc_entry(loc: Location, arr: bool = True, dep: bool = True):
    entry = {
        "name": loc.name,
        "crs": loc.crs,
        "platform": loc.platform
    }
    if arr:
        entry["arr"] = make_planact_entry(loc.arr)
    if dep:
        entry["dep"] = make_planact_entry(loc.dep)
    return entry


def make_entry(service: Service, origin_crs: str, destination_crs: str, stock: str, mileage: Mileage):

    entry = {
        "date": {
            "year": service.date.year,
            "month": service.date.month,
            "day": service.date.day,
        },
        "operator": service.toc,
        "operator_code": service.tocCode,
        "mileage": {
            "miles": mileage.miles,
            "chains": mileage.chains
        },
        "uid": service.uid,
        "headcode": service.headcode,
        "stock": stock,
        "origins": list(map(make_short_loc_entry, service.origins)),
        "destinations": list(map(make_short_loc_entry, service.destinations)),
    }

    boarded = False
    stop_entries = []
    for loc in service.calls:
        if not boarded:
            if loc.crs == origin_crs:
                boarded = True
                entry["origin"] = make_loc_entry(loc, False, True)
                origin_time = loc.dep
        else:
            if loc.crs == destination_crs:
                entry["destination"] = make_loc_entry(loc, True, False)
                destination_time = loc.dep
            else:
                stop_entries.append(make_loc_entry(loc))

    entry["stops"] = stop_entries

    duration_plan = get_hourmin_string(
        get_duration(origin_time.plan, destination_time.plan))
    duration = {
        "plan": duration_plan
    }

    if destination_time.act is not None and origin_time.act is not None:
        duration_act = get_duration(origin_time.act, destination_time.act)
        duration["act"] = duration_act
        entry["speed"] = get_mph_string(mileage.speed(duration_act))

    entry["duration"] = duration

    return entry


def get_date(start: date = None):
    if start is None:
        start = datetime.now().date()

    year = get_input_no(4, "Year", 2022, pad_front(start.year, 4))
    month = get_input_no(2, "Month", 12, pad_front(start.month, 2))
    max_days = get_month_length(int(month), int(year))
    day = get_input_no(2, "Day", max_days, pad_front(start.day, 2))
    return date(year, month, day)


def get_time(start: time = None):
    if start is None:
        start = datetime.now().time()
    time = get_input_no(4, "Time", 2359, pad_front(
        start.hour, 2) + pad_front(start.minute, 2))
    return time(time[0:2], time[2:4])


def get_datetime(start: date = None):
    date = get_date(start)
    time = get_time()
    return datetime(date.year, date.month, date.day, time.hour, time.minute)


def record_new_leg(start: date):
    origin_crs = get_station_string()
    destination_crs = get_station_string()
    dt = get_datetime(start)
    time = get_time()
    origin_station = Station(origin_crs, time)
    service = get_service(origin_station, destination_crs)
    stock = get_stock(service)
    mileage = get_mileage()
    return make_entry(service, stock, mileage)


def write_journey(journey: list, output_file: str):
    pass


def record_new_journey(output_file):

    journey = []

    while True:
        leg = record_new_leg(time)
        journey.append(leg)
        choice = yes_or_no("Add another leg?")
        if not choice:
            break

    write_journey(journey, output_file)

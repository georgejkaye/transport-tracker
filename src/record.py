import yaml
from datetime import datetime, timedelta
from pathlib import Path
from api import filter_services_by_stop, filter_services_by_time, get_destinations_full, get_headcode_full, get_locs_full, get_operator_code_full, get_operator_full, get_origins_full, get_services, get_station_name, get_uid_full, request_station_at_time, service_to_string_full, service_to_string_full_from_station, short_service_string
from network import get_matching_station_names, station_codes, station_names, station_code_to_name, station_name_to_code, stock_dict
from debug import debug


def pad_front(string, length):
    """
    Add zeroes to the front of a number string until it is the desired length
    """
    string = str(string)
    return "0" * (length - len(string)) + string


def get_time_string(time):
    """
    Given a time object, turn it into a string of the form HHMM
    """
    return pad_front(time.hour, 2) + pad_front(time.minute, 2)


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


def get_station_string(prompt):
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
                resp = input("Did you mean " + name + "? (y/n) ")
                # Default answer is yes
                if resp == "y" or resp == "":
                    return string
            # Otherwise search for substrings in the full names of stations
            matches = get_matching_station_names(string.lower().strip())
            if len(matches) == 0:
                print("No matches found, try again")
                return ""
            if len(matches) == 1:
                return station_name_to_code[matches[0]]
            print("Multiple matches found: ")
            choice = pick_from_list(matches, "Select a station")
            if choice == "":
                return ""
            return station_name_to_code[choice]
        else:
            print("Search string must be at least three characters")
            return ""


def pick_from_list(choices, prompt, display=lambda x: x):
    """
    Let the user pick from a list of choices
    """
    for i, choice in enumerate(choices):
        print(str(i+1) + ": " + display(choice))
    # The last option is a cancel option, this returns ""
    print(str(len(choices) + 1) + ": Cancel")
    while True:
        resp = input(prompt + " (1-" + str(len(choices) + 1) + "): ")
        try:
            resp = int(resp)
            if resp == len(choices) + 1:
                return ""
            elif resp > 0 or resp < len(choices):
                return choices[resp-1]
        except:
            pass


def get_station_from_user(origin):
    """
    Get a datetime from the user, then find the station data for the origin at that time
    """
    now = datetime.now()
    year = get_input_no(4, "Year", 2022, pad_front(now.year, 4))
    month = get_input_no(2, "Month", 12, pad_front(now.month, 2))
    max_days = get_month_length(int(month), int(year))
    day = get_input_no(2, "Day", max_days, pad_front(now.day, 2))
    time = get_input_no(4, "Time", 2359, pad_front(
        now.hour, 2) + pad_front(now.minute, 2))
    # Make the request
    station_data = request_station_at_time(origin, year, month, day, time)
    return (station_data, year, month, day, time)


def compute_time_difference(t1, t2, plus=False):
    diff = int(t1) - int(t2)
    neg = False
    # To make things simpler, we deal with positive numbers for now
    if diff < 0:
        neg = True
        diff = -diff
    if diff % 100 >= 60:
        diff = diff - 40
    if diff >= 1200:
        diff - 2400
    if diff <= -1200:
        diff + 2400
    # Don't forget to negate the number again if necessary
    if neg:
        diff = -diff
    string = str(diff)
    if diff > 0 and plus:
        string = "+" + string
    return str(diff)


def mins_to_hours(mins):
    hours = int(int(mins) / 60)
    mins = int(mins) % 60
    return pad_front(hours, 2) + ":" + pad_front(mins, 2)


def tab(level):
    string = ""
    for _ in range(level):
        string = string + "  "
    return string


def get_status(diff):
    diff = int(diff)
    if diff <= -5:
        return "very-late"
    if diff < 0:
        return "late"
    if diff == 0:
        return "on-time"
    if diff < 5:
        return "early"
    return "very-early"


def make_loc_entry(loc, arr, dep):
    entry = {
        "name": loc["description"],
        "crs": loc["crs"],
    }
    if arr:
        entry["arr_plan"] = loc["gbttBookedArrival"]
        if loc["realtimeArrivalActual"]:
            entry["arr_act"] = loc["realtimeArrival"]
            diff = compute_time_difference(
                entry["arr_act"], entry["arr_plan"], True)
            entry["arr_diff"] = diff
            entry["arr_status"] = get_status(diff)
    if dep:
        entry["dep_plan"] = loc["gbttBookedDeparture"]
        if loc["realtimeDepartureActual"]:
            entry["dep_act"] = loc["realtimeDeparture"]
            diff = compute_time_difference(
                entry["dep_act"], entry["dep_plan"], True)
            entry["dep_diff"] = diff
            entry["dep_status"] = get_status(diff)
    if "platform" in loc:
        entry["platform"] = loc["platform"]
    return entry


def make_short_loc_entry(loc, arr):
    entry = {
        "name": loc["description"],
        "crs": station_name_to_code[loc["description"]]
    }
    if arr:
        entry["arr_plan"] = loc["publicTime"]
    else:
        entry["dep_plan"] = loc["publicTime"]
    return entry


def make_new_log_entry(year, month, day, service, origin, destination, stock, miles, chains, output_file):
    # start off with some basic info about the service

    service_origins = []
    for loc in get_origins_full(service):
        service_origins.append(make_short_loc_entry(loc, False))

    service_destinations = []
    for loc in get_destinations_full(service):
        service_destinations.append(make_short_loc_entry(loc, True))

    stops = []
    boarded = False
    for loc in get_locs_full(service):
        if not boarded:
            if loc["crs"] == origin:
                journey_origin = make_loc_entry(loc, False, True)
                boarded = True
        else:
            if loc["crs"] == destination:
                journey_destination = make_loc_entry(loc, True, False)
                break
            else:
                stops.append(make_loc_entry(loc, True, True))

    entry = {
        "year": year,
        "month": month,
        "day": day,
        "uid": get_uid_full(service),
        "headcode": get_headcode_full(service),
        "operator_code": get_operator_code_full(service),
        "operator": get_operator_full(service),
        "service_origin": service_origins,
        "service_destination": service_destinations,
        "journey_origin": journey_origin,
        "journey_destination": journey_destination,
        "stops": stops,
        "stock": stock,
        "miles": miles,
        "chains": chains
    }

    dur_plan = compute_time_difference(
        journey_destination["arr_plan"], journey_origin["dep_plan"], True)
    entry["dur_plan"] = mins_to_hours(dur_plan)

    if "arr_act" in journey_destination and "dep_act" in journey_origin:
        dur_act = compute_time_difference(
            journey_destination["arr_act"], journey_origin["dep_act"], False)
        entry["dur_act"] = mins_to_hours(dur_act)
        entry["dur_diff"] = mins_to_hours(
            compute_time_difference(dur_act, dur_plan, False))
        speed = ((int(miles) + (int(chains) / 80)) /
                 (int(dur_act) / 60), 2)
        entry["speed"] = "{:.2f}".format(speed)

    try:
        with open(output_file, "r") as logfile:
            cur_yaml = yaml.safe_load(logfile)
        if cur_yaml is not None:
            cur_yaml.append(entry)
    except:
        cur_yaml = [entry]

    with open(output_file, "w") as logfile:
        yaml.safe_dump(cur_yaml, logfile)


def record_new_journey(output_file):
    """
    Record a new journey in the logfile
    """

    origin = ""
    dest = ""
    while origin == "":
        origin = get_station_string("Origin")

    while dest == "":
        dest = get_station_string("Destination")

    (station_data, year, month, day, time) = get_station_from_user(origin)
    services = get_services(station_data)

    if services is not None:
        departure_station = get_station_name(station_data)
        # We want to search within a smaller timeframe
        timeframe = 15
        search_time = datetime(int(year), int(month), int(day),
                               int(time[0:2]), int(time[2:4]))
        earliest_time = get_time_string(
            search_time - timedelta(minutes=timeframe))
        latest_time = get_time_string(
            search_time + timedelta(minutes=timeframe))
        # The results encompass a ~1 hour period
        # We only want to check our given timeframe
        filtered_services = filter_services_by_time(
            services, earliest_time, latest_time)
        # We also only want services that stop at our destination
        filtered_services = filter_services_by_stop(
            filtered_services, origin, dest
        )

        debug("Searching for services from " + departure_station)
        choice = pick_from_list(
            filtered_services, "Pick a service", lambda x: service_to_string_full_from_station(x, origin))

        if choice != "":

            # Currently getting this automatically isn't implemented
            # We could trawl wikipedia and make a map of which trains operate which services
            # Or if know your train becomes part of the api
            stock = pick_from_list(
                stock_dict[get_operator_full(choice)], "Stock", lambda x: x
            )

            # If we can get a good distance set this could be automated
            miles = get_input_no(-1, "Miles")
            chains = get_input_no(2, "Chains", 79)

            make_new_log_entry(year, month, day, choice,
                               origin, dest, stock, miles, chains, output_file)

    else:
        print("No services found!")

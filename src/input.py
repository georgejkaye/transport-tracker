from datetime import datetime, timedelta
from api import filter_services_by_stop, filter_services_by_time, get_services, get_station_name, request_station_at_time, service_to_string_full, short_service_string
from network import get_matching_station_names, station_codes, station_names, station_code_to_name, station_name_to_code


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
                return station_name_to_code[string]
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
        print(str(i) + ": " + display(choice))
    # The last option is a cancel option, this returns ""
    print(str(len(choices)) + ": Cancel")
    while True:
        resp = input(prompt + " (0-" + str(len(choices)) + ") ")
        try:
            resp = int(resp)
            if resp == len(choices):
                return ""
            return choices[resp]
        except:
            pass


def record_new_journey():
    """
    Record a new journey in the logfile
    """
    # The default values use today's date
    now = datetime.now()
    # How much leeway to give the input time, in minutes
    timeframe = 15

    # Get the data from the user
    origin = ""
    dest = ""
    while origin == "":
        origin = get_station_string("Origin")

    while dest == "":
        dest = get_station_string("Destination")
    year = get_input_no(4, "Year", 2022, pad_front(now.year, 4))
    month = get_input_no(2, "Month", 12, pad_front(now.month, 2))
    max_days = get_month_length(int(month), int(year))
    day = get_input_no(2, "Day", max_days, pad_front(now.day, 2))
    time = get_input_no(4, "Time", 2359, pad_front(
        now.hour, 2) + pad_front(now.minute, 2))

    # Make the request
    station_data = request_station_at_time(origin, year, month, day, time)

    # We want to search within a smaller timeframe
    search_time = datetime(int(year), int(month), int(day),
                           int(time[0:2]), int(time[2:4]))
    earliest_time = get_time_string(search_time - timedelta(minutes=timeframe))
    latest_time = get_time_string(search_time + timedelta(minutes=timeframe))

    services = get_services(station_data)

    if services is not None:
        departure_station = get_station_name(station_data)
        # The results encompass a ~1 hour period
        # We only want to check our given timeframe
        filtered_services = filter_services_by_time(
            services, earliest_time, latest_time)
        # We also only want services that stop at our destination
        filtered_services = filter_services_by_stop(
            filtered_services, origin, dest
        )

        print("Searching for services from " + departure_station)
        choice = pick_from_list(
            filtered_services, "Pick a service", service_to_string_full)
        print(service_to_string_full(choice))

    else:
        print("No services found!")

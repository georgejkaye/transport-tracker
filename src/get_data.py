import os
import requests
import webbrowser
import yaml
from datetime import datetime, timedelta


rtt_credentials_file = os.path.dirname(
    os.path.realpath(__file__)) + "/rtt.credentials"

rtt_endpoint = "https://api.rtt.io/api/v1/json/"
station_endpoint = rtt_endpoint + "search/"
service_endpoint = rtt_endpoint + "service/"

railmiles_site = "https://my.railmiles.me/mileage-engine/"

with open("rtt.credentials", "r") as rtt_credentials:
    (usr, pwd) = rtt_credentials.read().splitlines()

with open("data/codes.yml", "r") as codefiles:
    stns = yaml.safe_load(codefiles)

# Extract the codes and names from
station_codes = []
station_names = []
station_code_to_name = {}
station_name_to_code = {}

for stn in stns:
    station_codes.append(stn["code"])
    station_names.append(stn["name"])
    station_code_to_name[stn["code"]] = stn["name"]
    station_name_to_code[stn["name"]] = stn["code"]

timeframe = 15


def request(url):
    """Make a request to a url and get its response"""
    print("Requesting " + url)
    response = requests.get(url, auth=(usr, pwd))
    return response


def get_month_length(month, year):
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    elif month in [4, 6, 9, 11]:
        return 30
    elif year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        return 29
    else:
        return 28


def pad_front(string, length):
    string = str(string)
    return "0" * (length - len(string)) + string


def get_matching_station_names(string):
    matches = []
    for name in station_names:
        if string.lower() in name.lower():
            matches.append(name)
    return matches


def get_station_string(prompt):
    """
    Get a string specifying a station from a user.
    Can either be a three letter code (in which case confirmation will be asked for)
    or a full station name
    """
    while True:
        string = input(prompt + ": ").upper()
        if len(string) >= 3:
            if string in station_codes:
                name = station_code_to_name[string]
                resp = input("Did you mean " + name + "? (y/n) ")
                if resp == "y" or resp == "":
                    return string
            matches = get_matching_station_names(string.lower().strip())
            if len(matches) == 0:
                print("No matches found, try again")
                return ""
            if len(matches) == 1:
                return station_name_to_code[string]
            print("Multiple matches found: ")
            for i, match in enumerate(matches):
                print(str(i) + ": " + match)
            print(str(len(matches)) + ": Cancel")
            while True:
                resp = input(
                    "Select a station (0-" + str(len(matches)) + ") ")
                try:
                    resp = int(resp)
                    if resp == len(matches):
                        return ""
                    return station_name_to_code[matches[int(resp)]]
                except:
                    pass
        else:
            print("Search string must be at least three characters")
            return ""


def get_input_no(length, prompt, upper=-1, default=-1):
    """
    Get a natural number of a given length from the user,
    optionally with an upper bound and a default value to use if no input is given
    """
    while True:
        prompt_string = prompt
        if default != -1:
            prompt_string = prompt_string + " (" + str(default) + ")"
        prompt_string = prompt_string + ": "
        string = input(prompt_string)
        if string == "" and default != -1:
            return default
        try:
            nat = int(string)
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


def request_station(origin, year, month, day, time, to):
    """Get the response for a station at a given time"""
    url = station_endpoint + origin + "/"
    if to != "":
        url = url + "to/" + to + "/"
    url = url + year + "/" + month + "/" + day + "/" + time
    return request(url)


def request_service(uid, year, month, day):
    """Get the response for a service on a given day"""
    return request(service_endpoint + uid + "/" + year + "/" + month + "/" + day)


def get_hourmin(time):
    return pad_front(time.hour, 2) + pad_front(time.minute, 2)


def short_service_string(service):
    return service["trainIdentity"] + " " + service["locationDetail"]["origin"][0]["publicTime"] + " " + service["locationDetail"]["origin"][0]["description"] + " to " + service["locationDetail"]["destination"][0]["description"]


# The default values use today's date
now = datetime.now()

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

# We want a somewhat fuzzy timeframe
search_time = datetime(int(year), int(month), int(day),
                       int(time[0:2]), int(time[2:4]))
earliest_time = get_hourmin(search_time - timedelta(minutes=timeframe))
latest_time = get_hourmin(search_time + timedelta(minutes=timeframe))

# Make the request
response = request_station(origin, year, month, day, time, dest)
# Did it work okay?
if response.status_code != 200:
    print(str(response.status_code) + ": error obtaining data")
    exit(1)
# Get out the data
station_data = response.json()
departure_station = station_data["location"]["name"]
print("Searching for services from " + departure_station)

if len(station_data["services"]) > 0:
    for i, service in enumerate(station_data["services"]):
        print(str(i) + ": " + short_service_string(service))

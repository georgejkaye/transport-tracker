import requests
import os

from debug import debug

rtt_credentials_file = "rtt.credentials"
rtt_endpoint = "https://api.rtt.io/api/v1/json/"
station_endpoint = rtt_endpoint + "search/"
service_endpoint = rtt_endpoint + "service/"


def authenticate():
    """
    Globally set the realtime trains username and password
    """

    with open(rtt_credentials_file, "r") as rtt_credentials:
        (new_usr, new_pwd) = rtt_credentials.read().splitlines()

    global usr
    usr = new_usr
    global pwd
    pwd = new_pwd


def request(url):
    """Make a request to a url and get its response"""
    debug("Requesting " + url)
    response = requests.get(url, auth=(usr, pwd))
    return response


def request_service_on_day(uid, year, month, day):
    """Get the response for a service on a given day"""
    response = request(service_endpoint + uid + "/" +
                       year + "/" + month + "/" + day)
    check_response(response)
    return response.json()


def check_response(response):
    # Did it work okay?
    if response.status_code != 200:
        print(str(response.status_code) + ": error obtaining data")
        exit(1)


def get_multiple_location_string(service, origin):
    if origin:
        end = "origin"
    else:
        end = "destination"

    for i, loc in enumerate(service["locationDetail"][end]):
        if i == 0:
            string = loc["description"]
        else:
            string = string + " and " + loc["description"]
    return string

# station methods


def request_station_at_time(origin, year, month, day, time):
    """Get the response for a station at a given time"""
    url = station_endpoint + origin + "/" + \
        year + "/" + month + "/" + day + "/" + time
    response = request(url)
    check_response(response)
    return response.json()


def get_services(station):
    return station["services"]


def filter_services_by_time(services, earliest_time, latest_time):
    filtered_services = []
    for service in services:
        dep = get_departure_time_from_current(service)
        if int(dep) >= int(earliest_time) and int(dep) <= int(latest_time):
            filtered_services.append(service)
    return filtered_services


def filter_services_by_stop(services, origin, station):
    date = services[0]["runDate"]
    year = date[0:4]
    month = date[5:7]
    day = date[8:10]
    filtered_services = []
    for service in services:
        service_data = request_service_on_day(
            get_service_uid(service), year, month, day)
        if stops_at_station(service_data, origin, station):
            filtered_services.append(service)
    return filtered_services


def get_station_name(station):
    return station["location"]["name"]

# full service methods


def get_locs(service):
    return service["locations"]


def stops_at_station(service, origin, station):
    locs = get_locs(service)
    reached = False
    for loc in locs:
        if not reached:
            if get_crs(loc) == origin:
                reached = True
        else:
            if get_crs(loc) == station:
                return True

    return False

# location methods


def get_crs(loc):
    if loc["crs"]:
        return loc["crs"]
    return ""

# station service methods


def get_departure_time_from_current(service):
    location_data = service["locationDetail"]
    if "realtimeDeparture" in location_data:
        return service["locationDetail"]["realtimeDeparture"]
    return service["locationDetail"]["gbttBookedDeparture"]


def get_service_uid(service):
    return service["serviceUid"]


def get_headcode(service):
    return service["trainIdentity"]


def get_departure_time_from_origin(service):
    return service["locationDetail"]["origin"][0]["publicTime"]


def get_realtime_departure_time_from_current(service):
    return service["locationDetail"]["realtimeDeparture"]


def get_origin(service):
    return get_multiple_location_string(service, True)


def get_destination(service):
    return get_multiple_location_string(service, False)


def short_service_string(service):
    return get_realtime_departure_time_from_current(service) + " // " + get_headcode(service) + " " + get_departure_time_from_origin(service) + " " + get_origin(service) + \
        " to " + get_destination(service)

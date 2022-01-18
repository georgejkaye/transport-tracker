import requests

rtt_endpoint = "https://api.rtt.io/api/v1/json/"
station_endpoint = rtt_endpoint + "search/"
service_endpoint = rtt_endpoint + "service/"


def authenticate(new_usr, new_pwd):
    """
    Globally set the realtime trains username and password
    """
    global usr
    usr = new_usr
    global pwd
    pwd = new_pwd


def request(url):
    """Make a request to a url and get its response"""
    print("Requesting " + url)
    response = requests.get(url, auth=(usr, pwd))
    return response


def request_service(uid, year, month, day):
    """Get the response for a service on a given day"""
    return request(service_endpoint + uid + "/" + year + "/" + month + "/" + day)


def request_station(origin, year, month, day, time, to):
    """Get the response for a station at a given time"""
    url = station_endpoint + origin + "/"
    if to != "":
        url = url + "to/" + to + "/"
    url = url + year + "/" + month + "/" + day + "/" + time
    response = request(url)
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


def get_station_name(station):
    return station["location"]["name"]

# service methods


def get_headcode(service):
    return service["trainIdentity"]


def get_departure_time(service):
    return service["locationDetail"]["origin"][0]["publicTime"]


def get_origin(service):
    return get_multiple_location_string(service, True)


def get_destination(service):
    return get_multiple_location_string(service, False)


def short_service_string(service):
    return get_headcode(service) + " " + get_departure_time(service) + " " + get_origin(service) + \
        " to " + get_destination(service)

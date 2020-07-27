import json
import requests
import os
import datetime

time_error = 10

credentials_file = os.path.dirname(os.path.realpath(__file__)) + "/credentials"

with open(credentials_file, "r") as creds:
    (usr, pwd) = creds.read().splitlines()

base = "https://api.rtt.io/api/v1/json/"
station_url = base + "search/"
service_url = base + "service/"


def request(url):
    print("Requesting " + url)
    response = requests.get(url, auth=(usr, pwd))
    return response


def request_station_ymdt(stn, year, month, day, time):
    return request(station_url + stn + "/" + year + "/" + month + "/" + day + "/" + time)


def request_service_ymdt(uid, year, month, day):
    return request(service_url + uid + "/" + year + "/" + month + "/" + day)


def check_if_number(num, upper=-1, default=-1):

    if num == "" and default != -1:
        return default

    try:
        nat = int(num)
        if nat > 0 and (upper == -1 or nat <= upper):
            return num
        else:
            return -2
    except:
        return -1


def pad_front(num, length):
    string = str(num)

    for i in range(length - len(string)):
        string = "0" + string

    return string


def date_and_time(year, month, day, time):
    time = pad_front(time, 4)

    return pad_front(year, 4) + "/" + pad_front(month, 2) + "/" + pad_front(day, 2) + " " + time[:2] + ":" + time[2:]


def time_string(time):
    if len(time) == 4:
        return time[:2] + ":" + time[2:]

    seconds = time[4:6]

    if(seconds == "00"):
        seconds = ""
    elif(seconds == "15"):
        seconds = "¼"
    elif(seconds == "30"):
        seconds = "½"
    elif(seconds == "45"):
        seconds = "¾"

    return time[:2] + ":" + time[2:4] + seconds


def service_at_station_string(service):

    origin = service["locationDetail"]["origin"]
    destination = service["locationDetail"]["destination"]

    train_id = service["trainIdentity"]
    origin_departure = origin[0]["publicTime"]
    origin_description = origin[0]["description"]
    destination_description = destination[0]["description"]
    toc_name = service["atocName"]
    departure = service["locationDetail"]["gbttBookedDeparture"]

    return train_id + " " + origin_departure + " " + origin_description + " to " + destination_description + " (" + toc_name + ") dep " + time_string(departure)


def service_string(service):
    origin = service["origin"]
    destination = service["destination"]

    train_id = service["trainIdentity"]
    origin_departure = origin[0]["publicTime"]
    origin_description = origin[0]["description"]
    destination_description = destination[0]["description"]
    toc_name = service["atocName"]

    return train_id + " " + origin_departure + " " + origin_description + " to " + destination_description + " (" + toc_name + ")"


time_format = False

stn = input("Station: ")

day_format = False
month_format = False
year_format = False
time_format = False

current_year = pad_front(str(datetime.datetime.now().year), 4)

while not year_format:
    year = check_if_number(
        input("Year (" + current_year + "): "), -1, current_year)
    if year == -1:
        print("Not a number")
    else:
        year = pad_front(year, 4)
        year_format = True

leap_year = False

if (int(year) % 400 == 0) or ((int(year) % 4 == 0) and not (int(year) % 100 == 0)):
    leap_year = True

current_month = pad_front(str(datetime.datetime.now().month), 2)

while not month_format:
    month = check_if_number(
        input("Month (" + current_month + "): "), 12, current_month)
    if month == -1:
        print("Not a number")
    elif month == -2:
        print("Number not in range")
    else:
        month = pad_front(month, 2)
        month_format = True

current_day = pad_front(str(datetime.datetime.now().day), 2)

while not day_format:
    if (month in [1, 3, 5, 7, 8, 10, 12]):
        max_day = 31
    elif (month in [4, 6, 9, 11]):
        max_day = 30
    elif leap_year:
        max_day = 29
    else:
        max_day = 28

    day = check_if_number(
        input("Day (" + current_day + "): "), max_day, current_day)

    if day == -1:
        print("Not a number")
    elif day == -2:
        print("Number not in range")
    else:
        day = pad_front(day, 2)
        day_format = True

current_time = pad_front(str(datetime.datetime.now().hour), 2) + \
    pad_front(str(datetime.datetime.now().minute), 2)

while not time_format:
    time = check_if_number(
        input("Planned departure time (" + current_time + "): "), 2359, current_time)
    if time == -1:
        print("Not a number")
    elif time == -2:
        print("Number not in range")
    else:
        earliest_time = int(time) - time_error

        if(earliest_time < 0):
            earlist_time = earlist_time + 2400

        latest_time = int(time) + time_error

        if(latest_time >= 2400):
            latest_time = latest_time - 2400

        time = pad_front(time, 4)
        time_format = True


print("Searching " + stn + " at " + date_and_time(year, month, day, time))

response = request_station_ymdt(stn, year, month, day, time)

if (response.status_code != 200):
    print(str(response.status_code) + ": Could not get data")
    exit(1)

print("200 OK")

station_data = response.json()

departure_station = station_data["location"]["name"]

potential_services = []

for service in station_data["services"]:

    departure = int(service["locationDetail"]["gbttBookedDeparture"])

    if (departure >= earliest_time and departure <= latest_time):
        potential_services.append(service)


i = 1

number_of_services = len(potential_services)

for service in potential_services:
    print(str(i) + ": " + service_at_station_string(service))
    i = i + 1

choice_format = False

while not choice_format:
    chosen_service = input(
        "Pick a train (1-" + str(number_of_services) + "): ")
    chosen_service = check_if_number(chosen_service, number_of_services)

    if chosen_service == -1:
        print("Not a number")
    elif chosen_service == -2:
        print("Not in range")
    else:
        chosen_service = potential_services[int(chosen_service) - 1]
        choice_format = True

response = request_service_ymdt(
    chosen_service["serviceUid"], year, month, day)

if (response.status_code != 200):
    print(response.status_code + ": Could not get data")
    exit(1)

print("200 OK")

service_data = response.json()

on_train = False
stops = []

for location in service_data["locations"]:

    if on_train:
        stops.append(location["description"])
    elif location["crs"] == stn:
        on_train = True

i = 1

print(service_string(service_data) + " joined at " + departure_station)

for stop in stops:
    print(str(i) + ": " + stop)
    i = i + 1

dest = input("Pick a destination (1-" + str(len(stops)) + "): ")

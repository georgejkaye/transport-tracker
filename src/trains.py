import json
import requests
import os

time_error = 10

credentials_file = os.path.dirname(os.path.realpath(__file__)) + "/credentials"

with open(credentials_file, "r") as creds:
    (usr, pwd) = creds.read().splitlines()

base = "https://api.rtt.io/api/v1/json/"
station = base + "search/"
train = base + "service/"


def request(url):
    print("Requesting " + url)
    response = requests.get(url, auth=(usr, pwd))
    return response


def request_ymdt(stn, year, month, day, time):
    return request(station + stn + "/" + year + "/" + month + "/" + day + "/" + time)


def check_if_number(num, upper=-1):

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


def train_string(service):

    origin = service["locationDetail"]["origin"]
    destination = service["locationDetail"]["destination"]

    train_id = service["trainIdentity"]
    origin_departure = origin[0]["publicTime"]
    origin_description = origin[0]["description"]
    destination_description = destination[0]["description"]
    toc_name = service["atocName"]

    return (train_id + " " + origin_departure + " " + origin_description + " to " + destination_description + " (" + toc_name + ")")


time_format = False

stn = input("Station: ")

day_format = False
month_format = False
year_format = False
time_format = False

while not year_format:
    year = check_if_number(input("Year: "))
    if year == -1:
        print("Not a number")
    else:
        year = pad_front(year, 4)
        year_format = True

leap_year = False

if (int(year) % 400 == 0) or ((int(year) % 4 == 0) and not (int(year) % 100 == 0)):
    leap_year = True

while not month_format:
    month = check_if_number(input("Month: "), 12)
    if month == -1:
        print("Not a number")
    elif month == -2:
        print("Number not in range")
    else:
        month = pad_front(month, 2)
        month_format = True

while not day_format:
    if (month in [1, 3, 5, 7, 8, 10, 12]):
        max_day = 31
    elif (month in [4, 6, 9, 11]):
        max_day = 30
    elif leap_year:
        max_day = 29
    else:
        max_day = 28

    day = check_if_number(input("Day: "), max_day)

    if day == -1:
        print("Not a number")
    elif day == -2:
        print("Number not in range")
    else:
        day = pad_front(day, 2)
        day_format = True

while not time_format:
    time = check_if_number(input("Planned departure time: "), 2359)
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


print(date_and_time(year, month, day, time))

response = request_ymdt(stn, year, month, day, time)

if (response.status_code != 200):
    print(response.status_code + ": Could not get data")
    exit(1)

print("200 OK")

data = response.json()

potential_services = []

for service in data["services"]:

    departure = int(service["locationDetail"]["gbttBookedDeparture"])

    if (departure >= earliest_time and departure <= latest_time):
        potential_services.append(service)


i = 1

for service in potential_services:
    print(str(i) + ": " + train_string(service))
    i = i + 1

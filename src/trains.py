import json
import requests

with open("credentials", "r") as creds:
    (usr, pwd) = creds.read().splitlines()

base = "https://api.rtt.io/api/v1/json/"
station = base + "search/"
train = base + "serivce/"


def request(url):
    response = requests.get(url, auth=(usr, pwd))
    return response


def check_if_number(num, upper=-1):

    try:
        nat = int(num)
        if nat > 0 and (upper == -1 or nat <= upper):
            return nat
        else:
            return -2
    except:
        return -1


def pad_front(num, length):
    string = str(num)

    for i in range(length - len(string)):
        string = "0" + string

    return string


def date_and_time(time, day, month, year):
    time = pad_front(time, 4)

    return time[:2] + ":" + time[2:] + " " + pad_front(day, 2) + "/" + pad_front(month, 2) + "/" + str(year)


time_format = False

stn = input("Station: ")

day_format = False
month_format = False
year_format = False
time_format = False

while not year_format:
    year = check_if_number(input("Year: "))
    if year:
        year_format = True
    else:
        print("Bad year")

leap_year = False

if (year % 400 == 0) or ((year % 4 == 0) and not (year % 100 == 0)):
    leap_year = True

while not month_format:
    month = check_if_number(input("Month: "), 12)
    if month == -1:
        print("Not a number")
    elif month == -2:
        print("Number not in range")
    else:
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
        day_format = True

while not time_format:
    time = check_if_number(input("Time: "), 2359)
    if time == -1:
        print("Not a number")
    elif time == -2:
        print("Number not in range")
    else:
        time_format = True


print(date_and_time(time, day, month, year))

response = request(station + stn + "/")
print(response.status_code)

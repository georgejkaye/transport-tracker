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


response = request(station + "BMH")
print(response.status_code)

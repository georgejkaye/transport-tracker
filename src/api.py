from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Any

import requests

from debug import debug_msg

rtt_credentials_file = "rtt.credentials"
rtt_endpoint = "https://api.rtt.io/api/v1/json/"
station_endpoint = rtt_endpoint + "search"
service_endpoint = rtt_endpoint + "service"


@dataclass
class Credentials:
    usr: str
    pwd: str


def authenticate() -> Credentials:
    try:
        with open(rtt_credentials_file, "r") as rtt_credentials:
            (usr, pwd) = rtt_credentials.read().splitlines()
            return Credentials(usr, pwd)

    except:
        print("Could not open rtt.credentials.")
        exit(1)


def request(url: str, credentials: Credentials):
    """Make a request to a url and get its response"""
    debug_msg("Requesting " + url)
    response = requests.get(url, auth=(credentials.usr, credentials.pwd))
    return response


def check_response(response):
    # Did it work okay?
    if response.status_code != 200:
        print(f"{str(response.status_code)}: {response.content}")
        exit(1)


def request_service(uid: str, service_date: date, credentials: Credentials) -> Dict[str, Any]:
    date_string = service_date.strftime("%Y/%m/%d")
    response = request(f"{service_endpoint}/{uid}/{date_string}", credentials)
    check_response(response)
    return response.json()


def request_station(crs: str, search_datetime: datetime, credentials: Credentials) -> Dict[str, Any]:
    date_string = search_datetime.strftime("%Y/%m/%d")
    response = request(f"{station_endpoint}/{crs}/{date_string}", credentials)
    check_response(response)
    return response.json()

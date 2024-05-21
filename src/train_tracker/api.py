from dataclasses import dataclass

import requests

from train_tracker.debug import debug_msg

rtt_credentials_file = "rtt.credentials"
rtt_endpoint = "https://api.rtt.io/api/v1/json/"
station_endpoint = rtt_endpoint + "search/"
service_endpoint = rtt_endpoint + "service/"


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
        raise Exception(f"{str(response.status_code)}: {response.content}")

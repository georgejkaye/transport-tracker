import requests

from debug import debug

rtt_credentials_file = "rtt.credentials"
rtt_endpoint = "https://api.rtt.io/api/v1/json/"
station_endpoint = rtt_endpoint + "search/"
service_endpoint = rtt_endpoint + "service/"


def authenticate():
    """
    Globally set the realtime trains username and password
    """

    global usr
    global pwd

    try:
        with open(rtt_credentials_file, "r") as rtt_credentials:
            (usr, pwd) = rtt_credentials.read().splitlines()
    except:
        print("Could not open rtt.credentials.")
        exit(1)


def request(url: str):
    """Make a request to a url and get its response"""
    debug("Requesting " + url)
    response = requests.get(url, auth=(usr, pwd))
    return response


def check_response(response):
    # Did it work okay?
    if response.status_code != 200:
        print(f"{str(response.status_code)}: {response.content}")
        exit(1)

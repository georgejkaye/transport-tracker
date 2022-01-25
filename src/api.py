import datetime
import string
from httplib2 import Response
import requests
import os

from debug import debug
from network import lnwr_dests
from time import url

rtt_credentials_file = "rtt.credentials"
rtt_endpoint = "https://api.rtt.io/api/v1/json/"
station_endpoint = rtt_endpoint + "search/"
service_endpoint = rtt_endpoint + "service/"

usr = ""
pwd = ""


def authenticate():
    """
    Globally set the realtime trains username and password
    """

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

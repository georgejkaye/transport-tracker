from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from api import Credentials, request_station
from user.choice import pick_from_list, yes_or_no
from structs.network import Network, get_matching_station_names, get_station_crs_from_name, get_station_name_from_crs
from structs.service import Service, make_service, Station

# How many minutes leeway to give a search time
leeway = 15


def get_station_endpoint(crs: str, search_time: datetime) -> str:
    datetime_string = search_time.strftime("%Y/%m/d/%H%M")
    return f"https://www.realtimetrains.co.uk/service/gb-nr:{crs}/{datetime_string}/detailed"


def make_station(crs: str, search_time: datetime, credentials: Credentials, network: Network) -> Station:
    station_json = request_station(crs, search_time, credentials)

    name = station_json["location"]["name"]
    tiploc = station_json["location"]["tiploc"]

    services: list[Service] = []

    for service in station_json["services"]:
        service_object = make_service(service["serviceUid"],
                                      search_time.date(), credentials, network)
        services.append(service_object)

    return Station(
        name,
        crs,
        search_time,
        tiploc,
        services
    )


def get_station_string(prompt: str, default_station: Optional[Station], network: Network) -> Optional[str]:
    """
    Get a string specifying a station from a user.
    Can either be a three letter code (in which case confirmation will be asked for)
    or a full station name
    """
    if default_station is not None:
        prompt = f"{prompt} ({get_station_name_from_crs(network, default_station.crs)})"
    prompt = f'{prompt}: '
    # Keep looping until we accept a station or abort
    while True:
        string = input(prompt).upper()
        # We only search for strings of length at least three, otherwise there would be loads
        if len(string) == 0 and default_station is not None:
            return default_station.crs
        if len(string) >= 3:
            # Check the three letter codes first
            if string in network.station_codes:
                name = get_station_name_from_crs(network, string)
                # Just check that it's right, often the tlc is a guess
                resp = yes_or_no(f"Did you mean {name}?")
                if resp:
                    return string
            # Otherwise search for substrings in the full names of stations
            matches = get_matching_station_names(
                network, string.lower().strip())
            if len(matches) == 0:
                print("No matches found, try again")
            elif len(matches) == 1:
                match = matches[0]
                resp = yes_or_no(f"Did you mean {match}?")
                if resp:
                    return get_station_crs_from_name(network, match)
            else:
                print("Multiple matches found: ")
                choice = pick_from_list(matches, "Select a station", True)
                if choice is not None:
                    return get_station_crs_from_name(network, choice)
        else:
            print("Search string must be at least three characters")


def get_origin_station_string(default_station: Optional[Station], network: Network) -> Optional[str]:
    return get_station_string("Origin", default_station, network)


def get_destination_station_string(default_station: Optional[Station], network: Network) -> Optional[str]:
    return get_station_string("Destination", default_station, network)

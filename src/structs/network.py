from dataclasses import dataclass
import yaml
from debug import error_msg
from dirs import stations_list, lnwr_file, stock_file


@dataclass
class Network:
    station_codes: list[str]
    station_names: list[str]
    station_code_to_name: dict[str, str]
    station_name_to_code: dict[str, str]
    lnwr_destinations: list
    stock_dict: dict[str, str]


def setup_network() -> Network:

    with open(lnwr_file) as data:
        lnwr_destinations = yaml.safe_load(data)

    with open(stock_file) as data:
        stock_dict = yaml.safe_load(data)

    with open(stations_list, "r") as data:
        stations = yaml.safe_load(data)

    station_codes: list[str] = []
    station_names: list[str] = []
    station_code_to_name: dict[str, str] = {}
    station_name_to_code: dict[str, str] = {}

    for station in stations:
        station_codes.append(station["code"])
        station_names.append(station["name"])
        station_code_to_name[station["code"]] = station["name"]
        station_name_to_code[station["name"].lower()] = station["code"]

    return Network(
        station_codes,
        station_names,
        station_code_to_name,
        station_name_to_code,
        lnwr_destinations,
        stock_dict
    )


def get_station_name_from_crs(network: Network, crs: str) -> str:
    return network.station_code_to_name[crs.upper()]


def get_station_crs_from_name(network: Network, name: str) -> str:
    try:
        return network.station_name_to_code[name.lower()]
    except:
        error_msg(f"Station name {name} not found...")
        error_msg(
            "This should not happen! Please file an issue at https://github.com/georgejkaye/train-tracker/issues")
        exit(1)


def get_matching_station_names(network: Network, string: str) -> list[str]:
    matches: list[str] = []
    for name in network.station_names:
        if string.lower() in name.lower():
            matches.append(name)
    return matches

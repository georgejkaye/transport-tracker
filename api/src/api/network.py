import yaml
from api.debug import error_msg
from api.dirs import stations_list, lnwr_file, stock_file

station_codes: list[str] = []
station_names: list[str] = []
station_code_to_name: dict[str, str] = {}
station_name_to_code: dict[str, str] = {}

with open(lnwr_file) as lnwr:
    lnwr_dests = yaml.safe_load(lnwr)

with open(stock_file) as stock:
    stock_dict = yaml.safe_load(stock)


def setup_network():
    with open(stations_list, "r") as codefiles:
        stations = yaml.safe_load(codefiles)

    for station in stations:
        station_codes.append(station["code"])
        station_names.append(station["name"])
        station_code_to_name[station["code"]] = station["name"]
        station_name_to_code[station["name"].lower()] = station["code"]


def get_station_name_from_crs(crs: str):
    return station_code_to_name[crs.upper()]


def get_station_crs_from_name(name: str):
    try:
        return station_name_to_code[name.lower()]
    except:
        error_msg(f"Station name {name} not found...")
        error_msg(
            "This should not happen! Please file an issue at https://github.com/georgejkaye/train-tracker/issues"
        )


def get_matching_station_names(string: str):
    matches: list[str] = []
    for name in station_names:
        if string.lower() in name.lower():
            matches.append(name)
    return matches

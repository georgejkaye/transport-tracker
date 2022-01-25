import yaml
from dirs import stations_list, lnwr_file, stock_file

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
        station_name_to_code[station["name"]] = station["code"]


def get_matching_station_names(string: str):
    matches: list[str] = []
    for name in station_names:
        if string.lower() in name.lower():
            matches.append(name)
    return matches

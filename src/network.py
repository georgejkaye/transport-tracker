import yaml

network_file = "data/codes.yml"

station_codes = []
station_names = []
station_code_to_name = {}
station_name_to_code = {}


def setup_network():
    with open(network_file, "r") as codefiles:
        stations = yaml.safe_load(codefiles)

    for station in stations:
        station_codes.append(station["code"])
        station_names.append(station["name"])
        station_code_to_name[station["code"]] = station["name"]
        station_name_to_code[station["name"]] = station["code"]


def get_matching_station_names(string):
    matches = []
    for name in station_names:
        if string.lower() in name.lower():
            matches.append(name)
    return matches

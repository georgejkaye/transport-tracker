import sys

from datetime import date
from api import authenticate
from user.choice import get_datetime
from structs.network import setup_network
from structs.service import get_short_service_name, make_service, search_for_services
from structs.station import get_destination_station_string, get_origin_station_string, make_station

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python " + sys.argv[0] + " <output>")
        exit(1)

    output_file = sys.argv[1]

    network = setup_network()
    credentials = authenticate()

    search_dt = get_datetime(None)
    origin_crs = get_origin_station_string(None, network)
    if origin_crs is not None:
        origin = make_station(origin_crs, search_dt, credentials, network)
    else:
        exit(1)
    destination_crs = get_destination_station_string(None, network)
    if destination_crs is not None:
        destination = make_station(
            destination_crs, search_dt, credentials, network)
    else:
        exit(1)

    services = search_for_services(origin, destination)
    for service in services:
        print(get_short_service_name(service))

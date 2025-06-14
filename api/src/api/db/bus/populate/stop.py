import csv
import string
import sys

from decimal import Decimal
from typing import Optional
from psycopg import Connection
from shapely import Point

from api.utils.interactive import information

from api.db.bus.stop import BusStopData, insert_bus_stops
from api.network.network import osgb36_to_wgs84_point

naptan_stops_csv_url = "https://beta-naptan.dft.gov.uk/Download/National/csv"

# NaPTAN stops csv path
# https://beta-naptan.dft.gov.uk/download/national
stops_csv = sys.argv[1]

atco_code_column = 0
naptan_code_column = 1
common_name_column = 4
landmark_column = 8
street_column = 10
crossing_column = 12
indicator_column = 14
bearing_column = 16
locality_column = 18
parent_locality_column = 19
grandparent_locality_column = 20
town_column = 21
suburb_column = 23
eastings_column = 27
northings_column = 28
stop_type_column = 31

stops: list[BusStopData] = []

standard_bus_stop_type = "BCT"
station_bus_stop_type = "BCS"
variable_bus_stop_type = "BCQ"


def string_to_optional_string(string: str) -> Optional[str]:
    if string == "":
        return None
    return string


def get_bus_stops_from_stops_csv(stops_csv_path: str) -> list[BusStopData]:
    with open(stops_csv_path) as f:
        reader = csv.reader(f, delimiter=",")
        header = True
        for row in reader:
            if header:
                header = False
            else:
                stop_type = row[stop_type_column]
                if stop_type in [
                    standard_bus_stop_type,
                    station_bus_stop_type,
                    variable_bus_stop_type,
                ]:
                    osgb36_point = Point(
                        int(row[eastings_column]), int(row[northings_column])
                    )
                    wgs84_point = osgb36_to_wgs84_point(osgb36_point)
                    stop = BusStopData(
                        row[atco_code_column],
                        row[naptan_code_column],
                        string.capwords(row[common_name_column]),
                        string_to_optional_string(
                            string.capwords(row[landmark_column])
                        ),
                        string.capwords(row[street_column]),
                        string_to_optional_string(
                            string.capwords(row[crossing_column])
                        ),
                        string_to_optional_string(row[indicator_column]),
                        string.capwords(row[bearing_column]),
                        string.capwords(row[locality_column]),
                        string_to_optional_string(
                            string.capwords(row[parent_locality_column])
                        ),
                        string_to_optional_string(
                            string.capwords(row[grandparent_locality_column])
                        ),
                        string_to_optional_string(
                            string.capwords(row[town_column])
                        ),
                        string_to_optional_string(
                            string.capwords(row[suburb_column])
                        ),
                        Decimal(wgs84_point.y),
                        Decimal(wgs84_point.x),
                    )
                    stops.append(stop)
    information(f"Retrieved {len(stops)} bus stops")
    return stops


def populate_bus_stops(conn: Connection, stops_csv: str):
    information("Retrieving bus stops")
    stops = get_bus_stops_from_stops_csv(stops_csv)
    information("Inserting bus stops")
    insert_bus_stops(conn, stops)

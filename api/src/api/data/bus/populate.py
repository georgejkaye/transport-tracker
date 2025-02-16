import csv
from decimal import Decimal
import sys
from typing import Optional
from api.network.network import osgb36_to_wgs84_point
from shapely import Point

from api.data.bus.stop import BusStopData, insert_bus_stops
from api.utils.database import connect

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

stops = []


def string_to_optional_string(string: str) -> Optional[str]:
    if string == "":
        return None
    return string


with open(stops_csv) as f:
    reader = csv.reader(f, delimiter=",")
    header = True
    for row in reader:
        if header:
            header = False
        else:
            if row[naptan_code_column] != "":
                osgb36_point = Point(
                    int(row[eastings_column]), int(row[northings_column])
                )
                wgs84_point = osgb36_to_wgs84_point(osgb36_point)
                stop = BusStopData(
                    row[atco_code_column],
                    row[naptan_code_column],
                    row[common_name_column],
                    row[landmark_column],
                    row[street_column].title(),
                    string_to_optional_string(row[crossing_column]),
                    string_to_optional_string(row[indicator_column]),
                    row[bearing_column],
                    row[locality_column],
                    string_to_optional_string(row[parent_locality_column]),
                    string_to_optional_string(row[grandparent_locality_column]),
                    string_to_optional_string(row[town_column]),
                    string_to_optional_string(row[suburb_column]),
                    Decimal(wgs84_point.y),
                    Decimal(wgs84_point.x),
                )
                stops.append(stop)

with connect(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]) as (conn, _):
    insert_bus_stops(conn, stops)

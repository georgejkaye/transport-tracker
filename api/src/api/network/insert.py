import sys

import osmnx as ox

from api.utils.database import connect
from api.network.network import insert_station_node_to_network
from api.data.points import get_station_points_from_crses

network = ox.load_graphml(sys.argv[1])

crs = sys.argv[2]

if len(sys.argv) == 3:
    platform = sys.argv[2]
else:
    platform = None

with connect() as conn:
    station_points = get_station_points_from_crses(conn, [(crs, platform)])

insert_station_node_to_network(
    network, crs, platform, station_points, project_network=True
)

ox.save_graphml(network, sys.argv[1])

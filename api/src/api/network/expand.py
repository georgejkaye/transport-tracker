import sys
import osmnx as ox

from api.utils.database import connect
from api.network.network import (
    insert_node_dict_to_network,
)
from api.db.train.stations import get_station_points

with connect() as conn:
    station_points = get_station_points(conn)

network = ox.load_graphml(sys.argv[1])
network = insert_node_dict_to_network(network, station_points)
ox.save_graphml(network, sys.argv[2])

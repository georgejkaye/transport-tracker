import sys

from api.db.train.points import get_station_points
from api.library.networkx import load_osmnx_graphml, save_osmnx_graphml
from api.network.network import (
    insert_node_dict_to_network,
)
from api.utils.database import connect_with_env

with connect_with_env() as conn:
    station_points = get_station_points(conn)

network = load_osmnx_graphml(sys.argv[1])
network = insert_node_dict_to_network(network, station_points)
save_osmnx_graphml(network, sys.argv[2])

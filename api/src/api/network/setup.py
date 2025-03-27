import sys
import osmnx as ox

from api.utils.database import connect
from api.network.network import (
    get_railway_network,
    insert_node_dict_to_network,
    osgb36,
    wgs84,
)
from api.data.stations import get_station_points
from api.utils.interactive import input_confirm

input = input_confirm("Download network?", default=False)

if input:
    network = get_railway_network(["England", "Wales", "Scotland"])
else:
    network = ox.load_graphml(sys.argv[1])

projected_network = ox.project_graph(network, to_crs=osgb36)

with connect() as conn:
    station_points = get_station_points(conn)

projected_network = insert_node_dict_to_network(
    projected_network, station_points, False
)

new_network = ox.project_graph(projected_network, to_crs=wgs84)

for node in network.nodes():
    node["x"] = round(node["x"], 16)
    node["y"] = round(node["y"], 16)

ox.save_graphml(new_network, sys.argv[2])

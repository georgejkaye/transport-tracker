import sys

from api.db.train.points import (
    get_station_points,
)
from api.library.networkx import (
    get_nodes,
    load_osmnx_graphml,
    project_graph,
    save_osmnx_graphml,
)
from api.network.network import (
    get_railway_network,
    insert_node_dict_to_network,
    osgb36,
    wgs84,
)
from api.utils.database import connect_with_env
from api.utils.interactive import input_confirm

input = input_confirm("Download network?", default=False)

if input:
    network = get_railway_network(["England", "Wales", "Scotland"])
else:
    network = load_osmnx_graphml(sys.argv[1])

projected_network = project_graph(network, to_crs=osgb36)

with connect_with_env() as conn:
    station_points = get_station_points(conn)

projected_network = insert_node_dict_to_network(
    projected_network, station_points, False
)

new_network = project_graph(projected_network, to_crs=wgs84)

for node in get_nodes(network):
    node["x"] = round(node["x"], 16)
    node["y"] = round(node["y"], 16)

save_osmnx_graphml(new_network, sys.argv[2])

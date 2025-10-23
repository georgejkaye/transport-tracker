import sys
from typing import Optional

from api.library.networkx import load_osmnx_graphml, save_osmnx_graphml
from api.network.network import insert_station_node_to_network
from api.utils.database import connect_with_env

network = load_osmnx_graphml(sys.argv[1])

crs = sys.argv[2]

platform: Optional[str] = None

if len(sys.argv) == 3:
    platform = sys.argv[2]

with connect_with_env() as conn:
    station_points = get_station_points_from_crses(conn, [(crs, platform)])

insert_station_node_to_network(
    network, crs, platform, station_points, project_network=True
)

save_osmnx_graphml(network, sys.argv[1])

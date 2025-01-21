import sys
import osmnx as ox

from api.data.database import connect
from api.data.network import (
    get_railway_network,
    insert_station_node_to_network,
    osgb36,
    wgs84,
)
from api.data.stations import get_station_points

network = get_railway_network(["Great Britain"])

projected_network = ox.project_graph(network, to_crs=osgb36)

with connect() as (conn, _):
    rows = conn.execute("SELECT * FROM Station")
    station_points = get_station_points(conn)
    for row in rows:
        station_crs = row[0]
        projected_network = insert_station_node_to_network(
            conn,
            projected_network,
            station_crs,
            None,
            station_points,
            project_network=False,
            insert_all_points=True,
        )[0]

new_network = ox.project_graph(projected_network, to_crs=wgs84)
ox.save_graphml(new_network, sys.argv[2])

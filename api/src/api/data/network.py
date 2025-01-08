from dataclasses import dataclass
from decimal import Decimal
import sys
from typing import TypedDict
import networkx as nx
import osmnx as ox
import geopandas as gpd

from pathlib import Path
from geopandas import GeoDataFrame, GeoSeries
from networkx import MultiDiGraph
from shapely import (
    Geometry,
    LineString,
    Point,
    line_locate_point,
    set_precision,
)
from networkx.classes.coreviews import AtlasView

from api.data.database import connect
from api.data.stations import get_station_lonlat_from_crs
from api.data.map import (
    LegLine,
    make_leg_map,
    make_leg_map_from_gml_file,
    make_leg_map_from_linestrings,
)

coordinate_precision = 0.000001
wgs84 = "EPSG:4326"
osgb36 = "EPSG:27700"


def get_railway_network(places: list[str | dict[str, str]]) -> MultiDiGraph:
    return ox.graph.graph_from_place(
        places,
        custom_filter='["railway" ~ "rail"]["service" != "siding"]["service" != "yard"][service != "spur"]["passenger" != "no"]',
    )


# def get_closest_point_on_network_to_point(
#     point: Point, network: MultiDiGraph
# ) -> tuple[int, int, int]:
#     gdf_nodes = ox.convert.graph_to_gdfs(
#         network,
#         nodes=True,
#         edges=False,
#         node_geometry=True,
#         fill_edge_geometry=False,
#     )
#     gdf_edges = ox.convert.graph_to_gdfs(
#         network,
#         nodes=False,
#         edges=True,
#         node_geometry=False,
#         fill_edge_geometry=True,
#     )
#     gdf_nodes["geometry"] = gdf_nodes.geometry.to_crs(gb_projection)
#     gdf_nodes["x"] = gdf_nodes["geometry"].x
#     gdf_nodes["y"] = gdf_nodes["geometry"].y
#     gdf_edges["geometry"] = gdf_edges.geometry.to_crs(gb_projection)
#     graph_attrs = {"crs": gb_projection}
#     proj_multidigraph = ox.convert.graph_from_gdfs(
#         gdf_nodes, gdf_edges, graph_attrs=graph_attrs
#     )

#     point_node_dict: dict[str, list] = {"col1": ["point"], "geometry": [point]}
#     point_node_gdf = gpd.GeoDataFrame(point_node_dict, crs=gb_projection)
#     point_node_gdf["geometry"] = point_node_gdf.geometry.to_crs(gb_projection)
#     point_proj_lon = point_node_gdf["geometry"].x[0]
#     point_proj_lat = point_node_gdf["geometry"].x[1]

#     return ox.distance.nearest_edges(
#         proj_multidigraph,
#         point_proj_lon,
#         point_proj_lat,
#         interpolate=None,
#         return_dist=True,
#     )


def get_latlon_string(point: Point) -> str:
    return f"{point.y}, {point.x}"


class EdgeTags(TypedDict):
    osmid: list[int]
    maxspeed: list[str]
    name: list[str]
    ref: str
    oneway: bool
    reversed: bool
    length: float
    tunnel: str
    bridge: list[str]
    geometry: LineString


@dataclass
class EdgeDetails:
    source: int
    target: int
    tags: EdgeTags


def get_edge_from_endpoints(
    network: MultiDiGraph, source: int, target: int
) -> EdgeDetails:
    return EdgeDetails(source, target, network[source][target][0])


def get_nearest_edge(network: MultiDiGraph, point: Point) -> EdgeDetails:
    (source, target, _) = ox.nearest_edges(network, point.x, point.y)
    return get_edge_from_endpoints(network, source, target)


def get_closest_edge_on_network_to_point(
    point: Point, network: MultiDiGraph
) -> EdgeDetails:
    edge = get_nearest_edge(network, point)
    return edge


def get_edge_weight(source, target, edge_dict) -> float:
    return edge_dict[0]["length"]


def find_path_between_nodes(
    network: MultiDiGraph, source: int, target: int
) -> list[LineString]:
    path = nx.shortest_path(network, source, target, weight=get_edge_weight)
    line_strings = []

    for i in range(0, len(path) - 1):
        source_node = path[i]
        target_node = path[i + 1]
        edge = get_edge_from_endpoints(network, source_node, target_node)
        if edge.tags.get("geometry") is not None:
            line_strings.append(edge.tags["geometry"])
        else:
            source_node = network.nodes[edge.source]
            source_x = source_node["x"]
            source_y = source_node["y"]
            source_point = Point(source_x, source_y)
            target_node = network.nodes[edge.target]
            target_x = target_node["x"]
            target_y = target_node["y"]
            target_point = Point(target_x, target_y)
            line_strings.append(LineString([source_point, target_point]))

    return line_strings


if __name__ == "__main__":
    network = ox.io.load_graphml(sys.argv[1])
    with connect() as (conn, _):
        uni_latlon = get_station_lonlat_from_crs(conn, "BHM")
        cdf_latlon = get_station_lonlat_from_crs(conn, "EDB")
    uni_edge = get_closest_edge_on_network_to_point(uni_latlon, network)
    cdf_edge = get_closest_edge_on_network_to_point(cdf_latlon, network)
    path = find_path_between_nodes(network, uni_edge.source, cdf_edge.target)
    html = make_leg_map_from_linestrings(path)
    with open("test.html", "w+") as f:
        f.write(html)
    html2 = make_leg_map_from_linestrings([uni_edge.tags["geometry"]])
    with open("test2.html", "w+") as f:
        f.write(html2)

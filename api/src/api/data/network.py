from dataclasses import dataclass
from decimal import Decimal
import sys
from typing import TypedDict
import networkx as nx
from numpy import insert
import osmnx as ox
import geopandas as gpd

from pathlib import Path
from geopandas import GeoDataFrame, GeoSeries
from networkx import MultiDiGraph
from psycopg import Connection
from shapely import LineString, Point
import shapely
from shapely.ops import split, snap
from networkx.classes.coreviews import AtlasView

from api.data.database import connect
from api.data.stations import get_station_lonlat_from_crs
from api.data.map import (
    LegLine,
    MapPoint,
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
    network: MultiDiGraph, point: Point
) -> EdgeDetails:
    edge = get_nearest_edge(network, point)
    return edge


def get_edge_weight(source, target, edge_dict) -> float:
    return edge_dict[0]["length"]


def find_path_between_nodes(
    network: MultiDiGraph, source: int | str, target: int | str
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


def get_nearest_point_on_linestring(point: Point, line: LineString) -> Point:
    return line.interpolate(line.project(point))


def split_linestring_at_point(
    line: LineString, point: Point
) -> tuple[LineString, LineString]:
    adjusted_line = snap(line, point, 0.01)
    if not adjusted_line.contains(point):
        raise RuntimeError("The point is not close enough to the line")
    splits = split(adjusted_line, point)
    segments = splits.geoms
    first_segment = segments[0]
    second_segment = segments[1]
    if isinstance(
        first_segment, shapely.geometry.linestring.LineString
    ) and isinstance(second_segment, shapely.geometry.linestring.LineString):
        return (first_segment, second_segment)
    raise RuntimeError("Could not split line string")


def insert_station_node_to_network(
    conn: Connection, network: MultiDiGraph, station_crs: str
) -> MultiDiGraph:
    point = get_station_lonlat_from_crs(conn, station_crs)
    edge = get_closest_edge_on_network_to_point(network, point)
    edge_geometry = edge.tags["geometry"]
    point_on_edge = get_nearest_point_on_linestring(point, edge_geometry)
    (first_segment, second_segment) = split_linestring_at_point(
        edge_geometry, point_on_edge
    )
    network.add_node(
        station_crs, id=station_crs, x=point_on_edge.x, y=point_on_edge.y
    )
    network.remove_edge(edge.source, edge.target)
    network.add_edge(
        edge.source,
        station_crs,
        geometry=first_segment,
        length=first_segment.length,
    )
    network.add_edge(
        station_crs,
        edge.target,
        geometry=second_segment,
        length=second_segment.length,
    )
    return network


if __name__ == "__main__":
    network = ox.io.load_graphml(sys.argv[1])
    crs1 = "BHM"
    crs2 = "EDB"
    with connect() as (conn, _):
        network = insert_station_node_to_network(conn, network, crs1)
        network = insert_station_node_to_network(conn, network, crs2)
        station1 = get_station_lonlat_from_crs(conn, crs1)
        station2 = get_station_lonlat_from_crs(conn, crs2)
    route = find_path_between_nodes(network, "BHM", "EDB")
    print(network["BHM"])
    html2 = make_leg_map_from_linestrings(
        [
            MapPoint(station1, "#0000ff", 10, "BHM"),
            MapPoint(station2, "#00ff00", 10, "BHM on line"),
        ],
        route,
    )
    with open("test2.html", "w+") as f:
        f.write(html2)

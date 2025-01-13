from pathlib import Path
from platform import architecture
import sys
from numpy import insert
from pydantic_core import MultiHostUrl
import shapely

from dataclasses import dataclass
from typing import TypedDict
import networkx as nx
import osmnx as ox

from osmnx import settings as oxsettings

from networkx import MultiDiGraph
from psycopg import Connection
from shapely import LineString, Point
from shapely import geometry, ops
from geopandas import GeoDataFrame

from api.data.database import connect
from api.data.stations import ShortTrainStation, get_station_lonlat_from_crs

coordinate_precision = 0.000001
wgs84 = "EPSG:4326"
osgb36 = "EPSG:27700"

oxsettings.useful_tags_node.append("name")
oxsettings.useful_tags_way.append("electrified")


def get_railway_network(places: list[str | dict[str, str]]) -> MultiDiGraph:
    return ox.graph.graph_from_place(
        places,
        custom_filter='["railway" ~ "rail"]["service" != "siding"]["service" != "yard"][service != "spur"]["passenger" != "no"]',
    )


def get_railway_stations(places: list[str | dict[str, str]]) -> GeoDataFrame:
    return ox.features.features_from_place(
        places, tags={"railway": "station", "network": "National Rail"}
    )


def read_network_from_file(path: Path | str) -> MultiDiGraph:
    network = ox.io.load_graphml(path)
    return network


def get_latlon_string(point: Point) -> str:
    return f"{point.y}, {point.x}"


def merge_linestrings(line_strings: list[LineString]) -> LineString:
    multi_line = geometry.MultiLineString(line_strings)
    line = ops.linemerge(multi_line)
    if not isinstance(line, geometry.LineString):
        raise RuntimeError("Not contiguous line strings")
    return line


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
    adjusted_line = ops.snap(line, point, 0.01)
    if not adjusted_line.contains(point):
        raise RuntimeError("The point is not close enough to the line")
    splits = ops.split(adjusted_line, point)
    segments = splits.geoms
    first_segment = segments[0]
    second_segment = segments[1]
    if isinstance(
        first_segment, shapely.geometry.linestring.LineString
    ) and isinstance(second_segment, shapely.geometry.linestring.LineString):
        return (first_segment, second_segment)
    raise RuntimeError("Could not split line string")


def insert_node_to_network(
    network: MultiDiGraph, point: Point, id: str
) -> MultiDiGraph:
    edge = get_closest_edge_on_network_to_point(network, point)
    edge_geometry = edge.tags["geometry"]
    point_on_edge = get_nearest_point_on_linestring(point, edge_geometry)

    source = network.nodes[edge.source]
    target = network.nodes[edge.target]
    source_point = Point(source["x"], source["y"])
    target_point = Point(target["x"], target["y"])
    source_distance = shapely.distance(point_on_edge, source_point)
    target_distance = shapely.distance(point_on_edge, target_point)

    if source_distance < 0.001:
        network = nx.relabel_nodes(network, {edge.source: id})
    elif target_distance < 0.001:
        network = nx.relabel_nodes(network, {edge.target: id})
    else:
        (first_segment, second_segment) = split_linestring_at_point(
            edge_geometry, point_on_edge
        )
        network.add_node(id, id=id, x=point_on_edge.x, y=point_on_edge.y)
        network.remove_edge(edge.source, edge.target)
        network.remove_edge(edge.target, edge.source)
        network.add_edge(
            edge.source,
            id,
            geometry=first_segment,
            length=first_segment.length,
        )
        network.add_edge(
            id,
            edge.source,
            geometry=first_segment.reverse(),
            length=first_segment.length,
        )
        network.add_edge(
            id,
            edge.target,
            geometry=second_segment,
            length=second_segment.length,
        )
        network.add_edge(
            edge.target,
            id,
            geometry=second_segment.reverse(),
            length=second_segment.length,
        )
    return network


def insert_station_node_to_network(
    conn: Connection, network: MultiDiGraph, station_crs: str
) -> MultiDiGraph:
    if network.has_node(station_crs):
        return network
    print(f"Inserting {station_crs}")
    point = get_station_lonlat_from_crs(conn, station_crs)
    return insert_node_to_network(network, point, station_crs)


def find_path_between_stations(
    network: MultiDiGraph,
    conn: Connection,
    origin_crs: str,
    destination_crs: str,
) -> LineString:
    network = insert_station_node_to_network(conn, network, origin_crs)
    network = insert_station_node_to_network(conn, network, destination_crs)
    path = find_path_between_nodes(network, origin_crs, destination_crs)
    return merge_linestrings(path)


if __name__ == "__main__":
    stations = get_railway_stations(["United Kingdom"])
    actual_stations = []
    for row in stations.itertuples():
        if (
            row.network == "National Rail"
            and str(row._50) != "nan"
            and isinstance(row.geometry, geometry.Point)
        ):
            print(f"{row._50}\t\t{row.name}\t\t\t\t\t\t{row.geometry}")
            actual_stations.append((row._50, row.name, row.geometry))
    print(len(actual_stations))
    with connect() as (conn, cur):
        for station in actual_stations:
            conn.execute(
                "UPDATE Station SET latitude = %s, longitude = %s WHERE station_crs = %s",
                [station[2].y, station[2].x, station[0]],
            )
        conn.commit()

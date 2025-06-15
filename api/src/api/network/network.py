import shapely
import networkx as nx
import osmnx as ox

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, TypedDict
from osmnx import settings as oxsettings
from networkx import MultiDiGraph
from shapely import LineString, Point
from shapely import geometry, ops
from geopandas import GeoDataFrame

from api.library.networkx import (
    add_edge,
    add_node,
    graph_from_place,
    has_edge,
    load_osmnx_graphml,
    nearest_edges,
    project_graph,
)
from api.library.shapely import get_distance
from api.db.train.points import StationPoint, string_of_station_point

coordinate_precision = 0.000001
wgs84 = "EPSG:4326"
osgb36 = "EPSG:27700"

oxsettings.useful_tags_node.append("name")
oxsettings.useful_tags_way.append("electrified")


def prepend_to_linestring(linestring: LineString, point: Point) -> LineString:
    new_coords = [point]
    for x, y in linestring.coords:
        new_coords.append(Point(x, y))
    return LineString(new_coords)


def append_to_linestring(linestring: LineString, point: Point) -> LineString:
    new_coords: list[Point] = []
    for x, y in linestring.coords:
        new_coords.append(Point(x, y))
    new_coords.append(point)
    return LineString(new_coords)


def crs_to_numbers(crs: str) -> str:
    first_num = ord(crs[0]) - 65
    second_num = ord(crs[1]) - 65
    third_num = ord(crs[2]) - 65
    return f"{first_num:02d}{second_num:02d}{third_num:02d}"


def get_railway_network(
    places: list[str | dict[str, str]],
) -> MultiDiGraph[int]:
    return graph_from_place(
        places,
        custom_filter='["railway" ~ "rail"]["service" != "siding"]["service" != "yard"][service != "spur"]["passenger" != "no"]',
    )


def get_railway_stations(places: list[str | dict[str, str]]) -> GeoDataFrame:
    return ox.features.features_from_place(
        places, tags={"railway": "station", "network": "National Rail"}
    )


def read_network_from_file(path: Path | str) -> MultiDiGraph[int]:
    network = load_osmnx_graphml(path)
    return network


def get_latlon_string(point: Point) -> str:
    return f"{point.y}, {point.x}"


def wgs84_to_osgb36_point(point: Point) -> Point:
    projection = ox.projection.project_geometry(
        point, crs=wgs84, to_crs=osgb36
    )[0]
    if not isinstance(projection, Point):
        raise RuntimeError("Projected a point to not a point")
    return projection


def osgb36_to_wgs84_point(point: Point) -> Point:
    projection = ox.projection.project_geometry(
        point, crs=osgb36, to_crs=wgs84
    )[0]
    if not isinstance(projection, Point):
        raise RuntimeError("Projected a point to not a point")
    return projection


def merge_linestrings(line_strings: list[LineString]) -> LineString:
    multi_line = geometry.MultiLineString(line_strings)
    line = ops.linemerge(multi_line)
    if not isinstance(line, geometry.LineString):
        raise RuntimeError("Not contiguous line strings")
    return line


class EdgeTags(TypedDict):
    osmid: list[int]
    maxspeed: Optional[list[str]]
    name: Optional[list[str]]
    ref: Optional[str]
    oneway: Optional[bool]
    reversed: Optional[bool]
    length: Optional[float]
    tunnel: Optional[str]
    bridge: Optional[list[str]]
    geometry: Optional[LineString]
    electrified: Optional[str]


def instantiate_edge_tags(data: dict[str, Any]) -> EdgeTags:
    edge_tags: EdgeTags = EdgeTags(
        data["osmid"],
        data.get("maxspeed"),
        data.get("name"),
        data.get("ref"),
        data.get("oneway"),
        data.get("reversed"),
        data.get("length"),
        data.get("tunnel"),
        data.get("bridge"),
        data.get("geometry"),
        data.get("electrified"),
    )  # type:ignore
    return edge_tags


@dataclass
class EdgeDetails:
    source: int
    target: int
    tags: EdgeTags


def get_edge_from_endpoints[T](
    network: MultiDiGraph[int], source: int, target: int
) -> EdgeDetails:
    edge = network[source][target]
    edge_tags = instantiate_edge_tags(edge)
    return EdgeDetails(source, target, edge_tags)


def get_nearest_edge(network: MultiDiGraph[int], point: Point) -> EdgeDetails:
    (source, target, _) = nearest_edges(network, point.x, point.y)
    return get_edge_from_endpoints(network, source, target)


def get_closest_edge_on_network_to_point(
    network: MultiDiGraph[int], point: Point
) -> EdgeDetails:
    edge = get_nearest_edge(network, point)
    return edge


def get_node_id_from_crs_and_platform(crs: str, platform: Optional[str]) -> int:
    """
    Node ids are encoded as 1xxxxxxabbccdd where

    xxx: crs of the station encoded as zero-padded two digit numbers
    (a = 01, b = 02 etc)
    a: 0 if the platform is a number, 1 if the platform is a letter
    bb: the platform number padded to two digits if a number, the numeric
    encoding of the platform letter if a number (a = 01, b = 02 etc)
    cc: the letter suffix of the platform encoded as a number if one is present,
    00 if there is no suffix
    """
    if platform is None:
        platform_string = "000000"
    else:
        if platform.isnumeric():
            platform_string = f"10{int(platform):02d}00"
        elif platform[0:-1].isnumeric():
            platform_letter = ord(platform[-1]) - 64
            platform_string = f"10{platform[0:-1]}{platform_letter:02d}"
        else:
            platform_string = f"11{ord(platform) - 64}00"
    first_num = ord(crs[0]) - 64
    second_num = ord(crs[1]) - 64
    third_num = ord(crs[2]) - 64
    node_id = int(
        f"1{first_num:02d}{second_num:02d}{third_num:02d}{platform_string}"
    )
    return node_id


def get_node_id_from_station_point(point: StationPoint) -> int:
    return get_node_id_from_crs_and_platform(point.crs, point.platform)


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


def remove_edge[T](network: MultiDiGraph[T], source: T, target: T) -> None:
    if has_edge(network, source, target):
        remove_edge(network, source, target)


def insert_node_to_network(
    network: MultiDiGraph[int],
    point: Point,
    id: int,
    project_network: bool = True,
) -> MultiDiGraph[int]:
    if network.has_node(id):
        return network

    if project_network:
        projected_network: MultiDiGraph[int] = project_graph(
            network, to_crs=osgb36
        )
    else:
        projected_network = network
    projected_point = wgs84_to_osgb36_point(point)

    edge = get_closest_edge_on_network_to_point(
        projected_network, projected_point
    )

    source = projected_network.nodes[edge.source]
    target = projected_network.nodes[edge.target]
    source_point = Point(source["x"], source["y"])
    target_point = Point(target["x"], target["y"])

    edge_geometry = edge.tags["geometry"]

    if edge_geometry is None:
        raise RuntimeError("Could not get edge geometry")

    point_on_edge = get_nearest_point_on_linestring(
        projected_point, edge_geometry
    )

    source_distance = get_distance(point_on_edge, source_point)
    target_distance = get_distance(point_on_edge, target_point)

    if source_distance < 0.001:
        projected_network = nx.relabel_nodes(
            projected_network, {edge.source: id}
        )
    elif target_distance < 0.001:
        projected_network = nx.relabel_nodes(
            projected_network, {edge.target: id}
        )
    else:
        (first_segment, second_segment) = split_linestring_at_point(
            edge_geometry, point_on_edge
        )
        add_node(
            projected_network,
            id,
            id=id,
            x=round(point_on_edge.x, 16),
            y=round(point_on_edge.y, 16),
        )
        remove_edge(projected_network, edge.source, edge.target)
        remove_edge(projected_network, edge.target, edge.source)
        if first_segment.coords[0] != source_point:
            first_segment = append_to_linestring(first_segment, point_on_edge)
        add_edge(
            network,
            edge.source,
            id,
            geometry=first_segment,
            length=first_segment.length,
            electrified=edge.tags.get("electrified"),
            maxspeed=edge.tags.get("maxspeed"),
        )
        add_edge(
            network,
            id,
            edge.source,
            geometry=first_segment.reverse(),
            length=first_segment.length,
            electrified=edge.tags.get("electrified"),
            maxspeed=edge.tags.get("maxspeed"),
        )
        if second_segment.coords[-1] != target_point:
            first_segment = prepend_to_linestring(second_segment, point_on_edge)
        add_edge(
            network,
            id,
            edge.target,
            geometry=second_segment,
            length=second_segment.length,
            electrified=edge.tags.get("electrified"),
            maxspeed=edge.tags.get("maxspeed"),
        )
        add_edge(
            network,
            edge.target,
            id,
            geometry=second_segment.reverse(),
            length=second_segment.length,
            electrified=edge.tags.get("electrified"),
            maxspeed=edge.tags.get("maxspeed"),
        )

    if project_network:
        return project_graph(projected_network, to_crs=wgs84)
    return projected_network


def insert_nodes_to_network(
    network: MultiDiGraph[int],
    stations: list[StationPoint],
    project_network: bool = True,
) -> MultiDiGraph[int]:
    for station in stations:
        print(f"Inserting {string_of_station_point(station)}")
        network = insert_node_to_network(
            network,
            station.point,
            get_node_id_from_station_point(station),
            project_network=project_network,
        )
    return network


def insert_node_dict_to_network(
    network: MultiDiGraph[int],
    stations: dict[str, dict[Optional[str], StationPoint]],
    project_network: bool = False,
) -> MultiDiGraph[int]:
    nodes: list[StationPoint] = []
    for station_key in stations.keys():
        for platform_key in stations[station_key].keys():
            nodes.append(stations[station_key][platform_key])
    return insert_nodes_to_network(network, nodes, project_network)


def insert_station_node_to_network(
    network: MultiDiGraph[int],
    station_crs: str,
    station_platform: Optional[str],
    station_points: dict[str, dict[Optional[str], StationPoint]],
    project_network: bool = True,
    insert_all_points: bool = False,
) -> tuple[MultiDiGraph[int], list[StationPoint]]:
    if (
        not insert_all_points
        and station_points[station_crs].get(station_platform) is not None
    ):
        nodes_to_insert = [station_points[station_crs][station_platform]]
    else:
        nodes_to_insert = [
            station_points[station_crs][key]
            for key in station_points[station_crs].keys()
        ]
    network = insert_nodes_to_network(
        network,
        nodes_to_insert,
        project_network=project_network,
    )
    return (network, nodes_to_insert)

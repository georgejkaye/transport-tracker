from pathlib import Path
import shapely

from dataclasses import dataclass
from typing import Optional, TypedDict
import networkx as nx
import osmnx as ox

from osmnx import settings as oxsettings

from networkx import MultiDiGraph
from psycopg import Connection
from shapely import LineString, Point
from shapely import geometry, ops
from geopandas import GeoDataFrame

from api.data.database import connect
from api.data.stations import (
    StationPoint,
    get_station_points_from_crses,
)

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
    new_coords = []
    for x, y in linestring.coords:
        new_coords.append(Point(x, y))
    new_coords.append(point)
    return LineString(new_coords)


def crs_to_numbers(crs: str) -> str:
    print(crs)
    first_num = ord(crs[0]) - 65
    second_num = ord(crs[1]) - 65
    third_num = ord(crs[2]) - 65
    return f"{first_num:02d}{second_num:02d}{third_num:02d}"


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
    for a_line in line_strings:
        for coord in a_line.coords:
            print(coord)
        print("\n\n")
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
    electrified: str


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
    if edge_dict[0].get("maxspeed") is None:
        max_speed = 1
    else:
        max_speed_value = edge_dict[0]["maxspeed"]
        if isinstance(max_speed_value, str):
            max_speed = int(max_speed_value.split(" ")[0])
        else:
            max_speed = max(
                [int(string.split(" ")[0]) for string in max_speed_value]
            )
    return edge_dict[0]["length"] / (max_speed * max_speed)


def get_node_id_from_crs_and_platform(crs: str, platform: Optional[str]) -> int:
    """
    Node ids are encoded as 1abbccdd where

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
    return int(
        f"1{first_num:02d}{second_num:02d}{third_num:02d}{platform_string}"
    )


def get_node_id(point: StationPoint) -> int:
    return get_node_id_from_crs_and_platform(point.identifier, point.platform)


def find_path_between_nodes(
    network: MultiDiGraph, source: StationPoint, target: StationPoint
) -> Optional[LineString]:
    path = nx.shortest_path(
        network,
        get_node_id(source),
        get_node_id(target),
        weight=get_edge_weight,
    )
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
            source_point = Point(round(source_x, 16), round(source_y, 16))
            target_node = network.nodes[edge.target]
            target_x = target_node["x"]
            target_y = target_node["y"]
            target_point = Point(round(target_x, 16), round(target_y, 16))
            line_strings.append(LineString([source_point, target_point]))
    if len(line_strings) == 0:
        return None
    try:
        return merge_linestrings(line_strings)
    except:
        return None


@dataclass
class StationPath:
    source: StationPoint
    target: StationPoint
    path: LineString


def find_paths_between_nodes(
    network: MultiDiGraph,
    sources: list[StationPoint],
    targets: list[StationPoint],
) -> list[StationPath]:
    paths = []
    for source in sources:
        for target in targets:
            path = find_path_between_nodes(network, source, target)
            if path is not None:
                paths.append(StationPath(source, target, path))
    return paths


def find_shortest_path_between_multiple_nodes(
    network: MultiDiGraph,
    sources: list[StationPoint],
    targets: list[StationPoint],
) -> Optional[StationPath]:
    paths = find_paths_between_nodes(network, sources, targets)
    if len(paths) == 0:
        return None
    return min(paths, key=lambda path: shapely.length(path.path))


def find_shortest_path_between_nodes(
    network: MultiDiGraph,
    sources: StationPoint,
    targets: StationPoint,
) -> Optional[StationPath]:
    return find_paths_between_nodes(network, [sources], [targets])[0]


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


def remove_edge(network: MultiDiGraph, source: int | str, target: int | str):
    if network.has_edge(source, target):
        print(f"Removing edge between {source} and {target}")
        network.remove_edge(source, target)
    else:
        print(f"No edge between {source} and {target}")


def insert_node_to_network(
    network: MultiDiGraph, point: Point, id: int, project_network: bool = True
) -> MultiDiGraph:
    if network.has_node(id):
        print(f"Network already has node {id}, skipping")
        return network
    else:
        print(f"Inserting {id}")

    if project_network:
        projected_network = ox.project_graph(network, to_crs=osgb36)
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

    if edge.tags.get("geometry") is not None:
        edge_geometry = edge.tags["geometry"]
    else:
        edge_geometry = LineString([source_point, target_point])

    point_on_edge = get_nearest_point_on_linestring(
        projected_point, edge_geometry
    )

    source_distance = shapely.distance(point_on_edge, source_point)
    target_distance = shapely.distance(point_on_edge, target_point)

    if source_distance < 0.001:
        projected_network = nx.relabel_nodes(
            projected_network, {edge.source: id}
        )
    elif target_distance < 0.001:
        projected_network = nx.relabel_nodes(
            projected_network, {edge.target: id}
        )
    else:
        print(f"Splitting {edge_geometry} at {point_on_edge}")
        (first_segment, second_segment) = split_linestring_at_point(
            edge_geometry, point_on_edge
        )
        projected_network.add_node(
            id,
            id=id,
            x=round(point_on_edge.x, 16),
            y=round(point_on_edge.y, 16),
        )
        remove_edge(projected_network, edge.source, edge.target)
        remove_edge(projected_network, edge.target, edge.source)
        if first_segment.coords[0] != source_point:
            first_segment = append_to_linestring(first_segment, point_on_edge)
        projected_network.add_edge(
            edge.source,
            id,
            geometry=first_segment,
            length=first_segment.length,
            electrified=edge.tags.get("electrified"),
            maxspeed=edge.tags.get("maxspeed"),
        )
        projected_network.add_edge(
            id,
            edge.source,
            geometry=first_segment.reverse(),
            length=first_segment.length,
            electrified=edge.tags.get("electrified"),
            maxspeed=edge.tags.get("maxspeed"),
        )
        if second_segment.coords[-1] != target_point:
            first_segment = prepend_to_linestring(second_segment, point_on_edge)
        projected_network.add_edge(
            id,
            edge.target,
            geometry=second_segment,
            length=second_segment.length,
            electrified=edge.tags.get("electrified"),
            maxspeed=edge.tags.get("maxspeed"),
        )
        projected_network.add_edge(
            edge.target,
            id,
            geometry=second_segment.reverse(),
            length=second_segment.length,
            electrified=edge.tags.get("electrified"),
            maxspeed=edge.tags.get("maxspeed"),
        )

    inserted_point_wgs84 = osgb36_to_wgs84_point(point_on_edge)
    print(f"{inserted_point_wgs84.y}, {inserted_point_wgs84.x}")

    if project_network:
        return ox.project_graph(projected_network, to_crs=wgs84)
    return projected_network


def insert_nodes_to_network(
    network: MultiDiGraph,
    stations: list[StationPoint],
    project_network: bool = True,
) -> MultiDiGraph:
    for station in stations:
        network = insert_node_to_network(
            network,
            station.point,
            get_node_id(station),
            project_network=project_network,
        )
    return network


def insert_node_dict_to_network(
    network: MultiDiGraph,
    stations: dict[str, dict[Optional[str], StationPoint]],
) -> MultiDiGraph:
    nodes = []
    for station_key in stations.keys():
        for platform_key in stations[station_key].keys():
            nodes.append(stations[station_key][platform_key])
    return insert_nodes_to_network(network, nodes)


def insert_station_node_to_network(
    conn: Connection,
    network: MultiDiGraph,
    station_crs: str,
    station_platform: Optional[str],
    station_points: dict[str, dict[Optional[str], StationPoint]],
    project_network: bool = True,
    insert_all_points: bool = False,
) -> tuple[MultiDiGraph, list[StationPoint]]:
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


def find_paths_between_stations(
    network: MultiDiGraph,
    conn: Connection,
    origin_crs: str,
    origin_platform: Optional[str],
    destination_crs: str,
    destination_platform: Optional[str],
    station_points: dict[str, dict[Optional[str], StationPoint]],
) -> tuple[MultiDiGraph, list[StationPath]]:
    print(
        f"{origin_crs}:{origin_platform} to {destination_crs}:{destination_platform}"
    )
    (network, origin_points) = insert_station_node_to_network(
        conn, network, origin_crs, origin_platform, station_points
    )
    (network, destination_points) = insert_station_node_to_network(
        conn, network, destination_crs, destination_platform, station_points
    )
    paths = find_paths_between_nodes(network, origin_points, destination_points)
    return (network, paths)


def find_shortest_path_between_stations(
    network: MultiDiGraph,
    conn: Connection,
    origin_crs: str,
    origin_platform: Optional[str],
    destination_crs: str,
    destination_platform: Optional[str],
    station_points: dict[str, dict[Optional[str], StationPoint]],
) -> tuple[MultiDiGraph, Optional[StationPath]]:
    (network, paths) = find_paths_between_stations(
        network,
        conn,
        origin_crs,
        origin_platform,
        destination_crs,
        destination_platform,
        station_points,
    )
    shortest_path = min(paths, key=lambda path: shapely.length(path.path))
    return (network, shortest_path)


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

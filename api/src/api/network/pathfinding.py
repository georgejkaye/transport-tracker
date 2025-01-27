from decimal import Decimal
from api.data.leg import ShortLeg
import networkx as nx
import shapely

from typing import Optional
from api.data.stations import StationPoint, get_relevant_station_points
from api.network.network import (
    get_edge_from_endpoints,
    get_node_id_from_station_point,
    insert_node_to_network,
    merge_linestrings,
)
from networkx import MultiDiGraph
from shapely import LineString, Point


def get_shortest_linestring(
    linestrings: list[tuple[StationPoint, StationPoint, LineString]]
) -> Optional[tuple[StationPoint, StationPoint, LineString]]:
    return min(
        linestrings,
        default=None,
        key=lambda linestring: shapely.length(linestring[2]),
    )


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
    return edge_dict[0]["length"] / max_speed


def find_path_betwen_network_nodes(
    network: MultiDiGraph, source_id: int, target_id: int
) -> Optional[LineString]:
    path = nx.shortest_path(
        network, source_id, target_id, weight=get_edge_weight
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
            source_point = Point(
                float(round(Decimal(source_x), 16)),
                float(round(Decimal(source_y), 16)),
            )
            target_node = network.nodes[edge.target]
            target_x = target_node["x"]
            target_y = target_node["y"]
            target_point = Point(
                float(round(Decimal(target_x), 16)),
                float(round(Decimal(target_y), 16)),
            )
            line_strings.append(LineString([source_point, target_point]))
    if len(line_strings) == 0:
        return None
    try:
        return merge_linestrings(line_strings)
    except:
        return None


def find_path_between_station_points(
    network: MultiDiGraph, source: StationPoint, target: StationPoint
) -> Optional[LineString]:
    source_id = get_node_id_from_station_point(source)
    target_id = get_node_id_from_station_point(target)
    if not network.has_node(source_id):
        insert_node_to_network(
            network, source.point, source_id, project_network=False
        )
    if not network.has_node(target_id):
        insert_node_to_network(
            network, target.point, target_id, project_network=False
        )
    return find_path_betwen_network_nodes(network, source_id, target_id)


def find_paths_between_nodes(
    network: MultiDiGraph,
    sources: list[StationPoint],
    targets: list[StationPoint],
) -> list[tuple[StationPoint, StationPoint, LineString]]:
    paths = []
    for source in sources:
        for target in targets:
            path = find_path_between_station_points(network, source, target)
            if path is not None:
                paths.append((source, target, path))
    return paths


def find_shortest_path_between_multiple_nodes(
    network: MultiDiGraph,
    sources: list[StationPoint],
    targets: list[StationPoint],
) -> Optional[tuple[StationPoint, StationPoint, LineString]]:
    paths = find_paths_between_nodes(network, sources, targets)
    if len(paths) == 0:
        return None
    return get_shortest_linestring(paths)


def find_shortest_path_between_nodes(
    network: MultiDiGraph,
    sources: StationPoint,
    targets: StationPoint,
) -> Optional[tuple[StationPoint, StationPoint, LineString]]:
    return find_shortest_path_between_multiple_nodes(
        network, [sources], [targets]
    )


def find_paths_between_stations(
    network: MultiDiGraph,
    origin_crs: str,
    origin_platform: Optional[str],
    destination_crs: str,
    destination_platform: Optional[str],
    station_points: dict[str, dict[Optional[str], StationPoint]],
) -> list[tuple[StationPoint, StationPoint, LineString]]:
    origin_points = get_relevant_station_points(
        origin_crs, origin_platform, station_points
    )
    destination_points = get_relevant_station_points(
        destination_crs, destination_platform, station_points
    )
    paths = find_paths_between_nodes(network, origin_points, destination_points)
    return paths


def find_shortest_path_between_stations(
    network: MultiDiGraph,
    origin_crs: str,
    origin_platform: Optional[str],
    destination_crs: str,
    destination_platform: Optional[str],
    station_points: dict[str, dict[Optional[str], StationPoint]],
) -> Optional[tuple[StationPoint, StationPoint, LineString]]:
    paths = find_paths_between_stations(
        network,
        origin_crs,
        origin_platform,
        destination_crs,
        destination_platform,
        station_points,
    )
    shortest_path = get_shortest_linestring(paths)
    return shortest_path


def get_linestring_for_leg(
    network: MultiDiGraph,
    leg: ShortLeg,
    station_points: dict[str, dict[Optional[str], StationPoint]],
) -> Optional[tuple[list[StationPoint], LineString]]:
    leg_calls = leg.calls
    complete_paths: list[tuple[list[StationPoint], Optional[LineString]]] = []
    for platform_key in station_points[leg_calls[0].station.crs].keys():
        complete_paths.append(
            (
                [station_points[leg_calls[0].station.crs][platform_key]],
                None,
            )
        )
    for call in leg_calls[1:]:
        call_paths = []
        points_to_test = station_points[call.station.crs]
        for platform_key in points_to_test.keys():
            platform_paths = []
            point_to_test = points_to_test[platform_key]
            for stations, complete_path in complete_paths:
                path = find_path_between_station_points(
                    network, stations[-1], point_to_test
                )
                if path is not None:
                    if complete_path is None:
                        new_path = path
                    else:
                        new_path = merge_linestrings([complete_path, path])
                    new_stations = stations + [point_to_test]
                    platform_paths.append((new_stations, new_path))
            call_paths = call_paths + platform_paths
        complete_paths = call_paths
    complete_path = min(
        complete_paths,
        default=None,
        key=lambda result: shapely.length(result[1]),
    )
    if complete_path is None:
        return None
    (station_path, line_path) = complete_path
    if line_path is None:
        return None
    return (station_path, line_path)

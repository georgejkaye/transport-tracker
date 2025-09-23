from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional, Sequence

from networkx import MultiDiGraph
from shapely import LineString, Point

from api.classes.network.map import (
    LegLineCall,
    LegLineGeometry,
    NetworkNode,
    NetworkNodePath,
)
from api.library.networkx import shortest_path
from api.library.shapely import get_length
from api.network.network import (
    get_edge_from_endpoints,
    merge_linestrings,
)


def get_shortest_network_node_path[T: NetworkNode](
    linestrings: list[NetworkNodePath[T]],
) -> Optional[NetworkNodePath[T]]:
    if len(linestrings) == 0:
        return None
    return min(
        linestrings,
        key=lambda linestring: get_length(linestring.line),
    )


def get_edge_weight(
    source_id: int, target_id: int, edge_tags: dict[str, Any]
) -> Optional[float]:
    max_speed_value = edge_tags.get("maxspeed")
    if max_speed_value is None:
        max_speed = 100
    elif isinstance(max_speed_value, str):
        max_speed = int(max_speed_value.split(" ")[0])
    else:
        max_speed = max(
            [int(string.split(" ")[0]) for string in max_speed_value]
        )
    length = edge_tags.get("length")
    if length is None:
        raise RuntimeError(f"Edge ({source_id} {target_id}) has no length")
    return length / max_speed


def find_path_betwen_node_ids(
    network: MultiDiGraph[int], source_id: int, target_id: int
) -> Optional[LineString]:
    path = shortest_path(network, source_id, target_id, weight=get_edge_weight)
    line_strings: list[LineString] = []
    for i in range(0, len(path) - 1):
        source_node = path[i]
        target_node = path[i + 1]
        edge = get_edge_from_endpoints(network, source_node, target_node)
        if edge.tags["geometry"] is not None:
            line_strings.append(edge.tags["geometry"])
        else:
            source_node_dict = network.nodes[edge.source]
            source_x = source_node_dict["x"]
            source_y = source_node_dict["y"]
            source_point = Point(
                float(round(Decimal(source_x), 16)),
                float(round(Decimal(source_y), 16)),
            )
            target_node_dict = network.nodes[edge.target]
            target_x = target_node_dict["x"]
            target_y = target_node_dict["y"]
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


def find_path_between_network_nodes[T: NetworkNode](
    network: MultiDiGraph[int], source: T, target: T
) -> Optional[LineString]:
    return find_path_betwen_node_ids(network, source.get_id(), target.get_id())


def find_paths_between_network_nodes[T: NetworkNode](
    network: MultiDiGraph[int],
    sources: list[T],
    targets: list[T],
) -> list[NetworkNodePath[T]]:
    paths: list[NetworkNodePath[T]] = []
    for source in sources:
        for target in targets:
            path = find_path_between_network_nodes(network, source, target)
            if path is not None:
                paths.append(NetworkNodePath(source, target, path))
    return paths


def find_shortest_path_between_network_nodes[T: NetworkNode](
    network: MultiDiGraph[int],
    origins: list[T],
    destinations: list[T],
) -> Optional[NetworkNodePath[T]]:
    paths = find_paths_between_network_nodes(
        network,
        origins,
        destinations,
    )
    shortest_path = get_shortest_network_node_path(paths)
    return shortest_path


def get_leg_line_geometry_for_leg[T: LegLineCall](
    network: MultiDiGraph[int], leg_points: Sequence[Sequence[T]]
) -> Optional[LegLineGeometry[T]]:
    complete_paths: list[tuple[list[T], Optional[LineString]]] = []
    first_call_points = leg_points[0]
    for platform_point in first_call_points:
        complete_paths.append(([platform_point], None))
    for call_points in leg_points[1:]:
        call_paths: list[tuple[list[T], Optional[LineString]]] = []
        for platform_point in call_points:
            platform_paths: list[tuple[list[T], Optional[LineString]]] = []
            for station_chain, complete_path in complete_paths:
                path = find_path_between_network_nodes(
                    network, station_chain[-1], platform_point
                )
                if path is None:
                    continue
                if complete_path is None:
                    new_path = path
                else:
                    new_path = merge_linestrings([complete_path, path])
                new_stations = station_chain + [platform_point]
                platform_paths.append((new_stations, new_path))
            call_paths = call_paths + platform_paths
        complete_paths = call_paths
    if len(complete_paths) == 0:
        return None
    shortest_path = min(
        complete_paths,
        key=lambda result: (
            get_length(result[1]) if result[1] is not None else float("inf")
        ),
    )
    (station_path, line_path) = shortest_path
    if line_path is None:
        return None
    return LegLineGeometry(station_path, line_path)

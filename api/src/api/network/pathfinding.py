from __future__ import annotations

from decimal import Decimal
from typing import Optional

import networkx as nx
from networkx import MultiDiGraph
from shapely import LineString, Point

from api.classes.network.map import (
    LegLineCall,
    LegLineGeometry,
    NetworkNode,
    NetworkNodePath,
)
from api.classes.train.legs import (
    DbTrainLegPointsOutData,
)
from api.library.shapely import get_length
from api.network.network import (
    EdgeDetails,
    get_edge_from_endpoints,
    get_node_id_from_network_node,
    merge_linestrings,
)


def get_shortest_network_node_path(
    linestrings: list[NetworkNodePath],
) -> Optional[NetworkNodePath]:
    if len(linestrings) == 0:
        return None
    return min(
        linestrings,
        key=lambda linestring: get_length(linestring.line),
    )


def get_edge_weight(edge: EdgeDetails) -> float:
    max_speed_value = edge.tags["maxspeed"]
    if max_speed_value is None:
        max_speed = 100
    elif isinstance(max_speed_value, str):
        max_speed = int(max_speed_value.split(" ")[0])
    else:
        max_speed = max(
            [int(string.split(" ")[0]) for string in max_speed_value]
        )
    if edge.tags["length"] is None:
        raise RuntimeError(f"Edge ({edge.source} {edge.target}) has no length")
    return edge.tags["length"] / max_speed


def find_path_betwen_node_ids(
    network: MultiDiGraph[int], source_id: int, target_id: int
) -> Optional[LineString]:
    path = nx.shortest_path(
        network, source_id, target_id, weight=get_edge_weight
    )
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


def find_path_between_network_nodes(
    network: MultiDiGraph[int], source: NetworkNode, target: NetworkNode
) -> Optional[LineString]:
    source_id = get_node_id_from_network_node(source)
    target_id = get_node_id_from_network_node(target)
    return find_path_betwen_node_ids(network, source_id, target_id)


def find_paths_between_network_nodes(
    network: MultiDiGraph[int],
    sources: list[NetworkNode],
    targets: list[NetworkNode],
) -> list[NetworkNodePath]:
    paths: list[NetworkNodePath] = []
    for source in sources:
        for target in targets:
            path = find_path_between_network_nodes(network, source, target)
            if path is not None:
                paths.append(NetworkNodePath(source, target, path))
    return paths


def find_shortest_path_between_network_nodes(
    network: MultiDiGraph[int],
    origins: list[NetworkNode],
    destinations: list[NetworkNode],
) -> Optional[NetworkNodePath]:
    paths = find_paths_between_network_nodes(
        network,
        origins,
        destinations,
    )
    shortest_path = get_shortest_network_node_path(paths)
    return shortest_path


def get_linestring_for_leg(
    network: MultiDiGraph[int], leg: DbTrainLegPointsOutData
) -> Optional[LegLineGeometry]:
    complete_paths: list[tuple[list[LegLineCall], Optional[LineString]]] = []
    first_call = leg.call_points[0]
    for platform_point in first_call.points:
        complete_paths.append(
            (
                [
                    LegLineCall(
                        first_call.station_id,
                        first_call.station_crs,
                        first_call.station_name,
                        first_call.platform,
                        platform_point.longitude,
                        platform_point.latitude,
                        first_call.plan_dep,
                        first_call.plan_arr,
                        first_call.act_dep,
                        first_call.act_arr,
                    )
                ],
                None,
            )
        )
    for call in leg.call_points[1:]:
        call_paths: list[tuple[list[LegLineCall], Optional[LineString]]] = []
        for platform_point in call.points:
            leg_line_call = LegLineCall(
                call.station_id,
                call.station_crs,
                call.station_name,
                call.platform,
                platform_point.longitude,
                platform_point.latitude,
                call.plan_dep,
                call.plan_arr,
                call.act_dep,
                call.act_arr,
            )
            platform_paths: list[
                tuple[list[LegLineCall], Optional[LineString]]
            ] = []
            for station_chain, complete_path in complete_paths:
                path = find_path_between_network_nodes(
                    network,
                    NetworkNode(
                        station_chain[-1].station_crs,
                        station_chain[-1].platform,
                    ),
                    NetworkNode(
                        leg_line_call.station_crs, leg_line_call.platform
                    ),
                )
                if path is None:
                    continue
                if complete_path is None:
                    new_path = path
                else:
                    new_path = merge_linestrings([complete_path, path])
                new_stations = station_chain + [leg_line_call]
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

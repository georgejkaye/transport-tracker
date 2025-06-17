from __future__ import annotations

import networkx as nx

from decimal import Decimal
from typing import Optional
from networkx import MultiDiGraph
from shapely import LineString, Point

from api.library.shapely import get_length
from api.classes.train.leg import ShortLegCall
from api.classes.train.station import PointTimes, StationPoint
from api.db.train.points import get_relevant_station_points
from api.network.network import (
    EdgeDetails,
    get_edge_from_endpoints,
    get_node_id_from_station_point,
    insert_node_to_network,
    merge_linestrings,
)


def get_shortest_linestring(
    linestrings: list[tuple[StationPoint, StationPoint, LineString]],
) -> Optional[tuple[StationPoint, StationPoint, LineString]]:
    if len(linestrings) == 0:
        return None
    return min(
        linestrings,
        key=lambda linestring: get_length(linestring[2]),
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


def find_path_betwen_network_nodes(
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


def find_path_between_station_points(
    network: MultiDiGraph[int], source: StationPoint, target: StationPoint
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
    network: MultiDiGraph[int],
    sources: list[StationPoint],
    targets: list[StationPoint],
) -> list[tuple[StationPoint, StationPoint, LineString]]:
    paths: list[tuple[StationPoint, StationPoint, LineString]] = []
    for source in sources:
        for target in targets:
            path = find_path_between_station_points(network, source, target)
            if path is not None:
                paths.append((source, target, path))
    return paths


def find_shortest_path_between_multiple_nodes(
    network: MultiDiGraph[int],
    sources: list[StationPoint],
    targets: list[StationPoint],
) -> Optional[tuple[StationPoint, StationPoint, LineString]]:
    paths = find_paths_between_nodes(network, sources, targets)
    if len(paths) == 0:
        return None
    return get_shortest_linestring(paths)


def find_shortest_path_between_nodes(
    network: MultiDiGraph[int],
    sources: StationPoint,
    targets: StationPoint,
) -> Optional[tuple[StationPoint, StationPoint, LineString]]:
    return find_shortest_path_between_multiple_nodes(
        network, [sources], [targets]
    )


def find_paths_between_stations(
    network: MultiDiGraph[int],
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
    network: MultiDiGraph[int],
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


def short_leg_call_to_point_times(leg_call: ShortLegCall) -> PointTimes:
    return PointTimes(
        leg_call.plan_arr, leg_call.plan_dep, leg_call.act_arr, leg_call.act_dep
    )


def get_linestring_for_leg(
    network: MultiDiGraph[int],
    leg_calls: list[ShortLegCall],
    station_points: dict[str, dict[Optional[str], StationPoint]],
) -> Optional[tuple[list[StationPoint], LineString]]:
    complete_paths: list[tuple[list[StationPoint], Optional[LineString]]] = []
    for platform_key in station_points[leg_calls[0].station.crs].keys():
        first_point = station_points[leg_calls[0].station.crs][platform_key]
        complete_paths.append(
            (
                [
                    StationPoint(
                        first_point.crs,
                        first_point.name,
                        first_point.platform,
                        first_point.point,
                        short_leg_call_to_point_times(leg_calls[0]),
                    )
                ],
                None,
            )
        )
    for call in leg_calls[1:]:
        call_paths: list[tuple[list[StationPoint], Optional[LineString]]] = []
        points_to_test = station_points[call.station.crs]
        for platform_key in points_to_test.keys():
            platform_paths: list[
                tuple[list[StationPoint], Optional[LineString]]
            ] = []
            point_to_test = points_to_test[platform_key]
            for stations, complete_path in complete_paths:
                path = find_path_between_station_points(
                    network, stations[-1], point_to_test
                )
                if path is None:
                    continue
                if complete_path is None:
                    new_path = path
                else:
                    new_path = merge_linestrings([complete_path, path])
                new_stations = stations + [
                    StationPoint(
                        point_to_test.crs,
                        point_to_test.name,
                        point_to_test.platform,
                        point_to_test.point,
                        short_leg_call_to_point_times(call),
                    )
                ]
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
    return (station_path, line_path)

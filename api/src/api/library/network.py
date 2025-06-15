"""
Wrapper file to hide away the mean type errors
"""

from pathlib import Path
from typing import Any, Optional
import osmnx as ox
from networkx import MultiDiGraph


def add_node[T](
    network: MultiDiGraph[T], node_for_adding: T, id: Any, x: float, y: float
):
    network.add_node(node_for_adding, id=id, x=x, y=y)  # type: ignore


def add_edge[T](network: MultiDiGraph[T], source: T, target: T, **attr: Any):
    network.add_edge(source, target, attr=attr)  # type: ignore


def has_edge[T](network: MultiDiGraph[T], source: T, target: T) -> bool:
    return network.has_edge(source, target)  # type: ignore


def remove_edge[T](network: MultiDiGraph[T], source: T, target: T) -> bool:
    return network.remove_edge(source, target)  # type: ignore


def load_osmnx_graphml(path: Path | str) -> MultiDiGraph[int]:
    return ox.load_graphml(path)  # type: ignore


def save_osmnx_graphml(network: MultiDiGraph[int], path: Path | str):
    ox.save_graphml(network, path)  # type: ignore


def project_graph[T](network: MultiDiGraph[T], to_crs: str) -> MultiDiGraph[T]:
    return ox.project_graph(network, to_crs)  # type: ignore


def graph_from_place(
    places: list[str | dict[str, str]], custom_filter: Optional[str] = None
) -> MultiDiGraph[int]:
    return ox.graph.graph_from_place(places, custom_filter=custom_filter)  # type: ignore


def nearest_edges(
    network: MultiDiGraph[int], x: float, y: float
) -> tuple[int, int, int]:
    return ox.nearest_edges(network, x, y)  # type: ignore

"""
Wrapper file to hide away the mean type errors
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterator, Optional

import networkx as nx
import osmnx as ox
from networkx import MultiDiGraph


def get_nodes[T](network: MultiDiGraph[T]) -> Iterator[dict[str, Any]]:
    return network.nodes()  # type: ignore[return-value]


def add_node[T](
    network: MultiDiGraph[T], node_for_adding: T, id: Any, x: float, y: float
) -> None:
    network.add_node(node_for_adding, id=id, x=x, y=y)  # type: ignore[no-untyped-call]


def add_edge[T](
    network: MultiDiGraph[T], source: T, target: T, **attr: Any
) -> None:
    network.add_edge(source, target, attr=attr)  # type: ignore[no-untyped-call]


def has_edge[T](network: MultiDiGraph[T], source: T, target: T) -> bool:
    return network.has_edge(source, target)  # type: ignore[no-untyped-call]


def remove_edge[T](network: MultiDiGraph[T], source: T, target: T) -> None:
    network.remove_edge(source, target)  # type: ignore[no-untyped-call]


def load_osmnx_graphml(path: Path | str) -> MultiDiGraph[int]:
    return ox.load_graphml(path)  # type: ignore[no-untyped-call]


def save_osmnx_graphml(network: MultiDiGraph[int], path: Path | str) -> None:
    ox.save_graphml(network, path)  # type: ignore[no-untyped-call]


def project_graph[T](network: MultiDiGraph[T], to_crs: str) -> MultiDiGraph[T]:
    return ox.project_graph(network, to_crs=to_crs)  # type: ignore[no-untyped-call]


def graph_from_place(
    places: str | list[str | dict[str, str]] | dict[str, Any],
    custom_filter: Optional[str] = None,
) -> MultiDiGraph[int]:
    return ox.graph.graph_from_place(places, custom_filter=custom_filter)  # type: ignore[no-untyped-call]


def nearest_edges(
    network: MultiDiGraph[int], x: float, y: float
) -> tuple[int, int, int]:
    return ox.nearest_edges(network, x, y)  # type: ignore[no-untyped-call]


def shortest_path[T](
    network: MultiDiGraph[T],
    source: T,
    target: T,
    weight: Callable[[T, T, dict[str, Any]], Optional[float]],
) -> list[T]:
    def weight_function(
        source: T, target: T, edge_dict: dict[int, dict[str, Any]]
    ) -> Optional[float]:
        return weight(source, target, edge_dict[0])

    return nx.shortest_path(network, source, target, weight=weight_function)  # type: ignore

"""
Wrapper file to hide away the mean type errors
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterator, Optional, cast

import networkx as nx
import osmnx as ox
from networkx import MultiDiGraph


def get_nodes[T](network: MultiDiGraph[T]) -> Iterator[dict[str, Any]]:
    return cast(Iterator[dict[str, Any]], cast(Any, network).nodes())


def add_node[T](
    network: MultiDiGraph[T], node_for_adding: T, id: Any, x: float, y: float
) -> None:
    cast(Any, network).add_node(node_for_adding, id=id, x=x, y=y)


def add_edge[T](
    network: MultiDiGraph[T], source: T, target: T, **attr: Any
) -> None:
    cast(Any, network).add_edge(source, target, attr=attr)


def has_edge[T](network: MultiDiGraph[T], source: T, target: T) -> bool:
    return cast(bool, cast(Any, network).has_edge(source, target))


def remove_edge[T](network: MultiDiGraph[T], source: T, target: T) -> None:
    cast(Any, network).remove_edge(source, target)


def load_osmnx_graphml(path: Path | str) -> MultiDiGraph[int]:
    return cast("MultiDiGraph[int]", cast(Any, ox).load_graphml(path))


def save_osmnx_graphml(network: MultiDiGraph[int], path: Path | str) -> None:
    cast(Any, ox).save_graphml(network, path)


def project_graph[T](network: MultiDiGraph[T], to_crs: str) -> MultiDiGraph[T]:
    return cast(
        "MultiDiGraph[T]", cast(Any, ox).project_graph(network, to_crs=to_crs)
    )


def graph_from_place(
    places: str | list[str | dict[str, str]] | dict[str, Any],
    custom_filter: Optional[str] = None,
) -> MultiDiGraph[int]:
    return cast(
        "MultiDiGraph[int]",
        cast(Any, ox.graph).graph_from_place(
            places, custom_filter=custom_filter
        ),
    )


def nearest_edges(
    network: MultiDiGraph[int], x: float, y: float
) -> tuple[int, int, int]:
    return cast(
        tuple[int, int, int], cast(Any, ox).nearest_edges(network, x, y)
    )


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

    return cast(
        list[T],
        cast(Any, nx).shortest_path(
            network, source, target, weight=weight_function
        ),
    )

"""
Wrapper file to hide away the mean type errors
"""

import osmnx as ox
from networkx import MultiDiGraph


def has_edge[T](network: MultiDiGraph[T], source: T, target: T) -> bool:
    return network.has_edge(source, target)  # type: ignore


def remove_edge[T](network: MultiDiGraph[T], source: T, target: T) -> bool:
    return network.remove_edge(source, target)  # type: ignore


def project_graph[T](network: MultiDiGraph[T], to_crs: str) -> MultiDiGraph[T]:
    return ox.project_graph(network, to_crs)  # type: ignore

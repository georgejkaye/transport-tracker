from collections import deque
from datetime import datetime

from api.pull.train.classes.gbnr.service import RttGbnrServiceData
from api.train.service.graph.classes import (
    ServiceGraphData,
    ServiceGraphEdgeData,
    ServiceGraphNode,
    ServiceGraphNodeData,
)
from api.utils.times import optional_isoformat


def serialise_service_graph(root: ServiceGraphNode) -> ServiceGraphData:
    node_ids: dict[int, str] = {}
    nodes: dict[str, ServiceGraphNodeData] = {}
    edges: dict[tuple[str, str, str], ServiceGraphEdgeData] = {}
    nodes_to_visit: deque[ServiceGraphNode] = deque()

    def get_node_id(node: ServiceGraphNode) -> str:
        identity = id(node)
        if identity not in node_ids:
            node_id = f"node-{len(node_ids)}"
            node_ids[identity] = node_id
            nodes_to_visit.append(node)
            location = node.location
            nodes[node_id] = ServiceGraphNodeData(
                id=node_id,
                location=location.description,
                short_codes=location.shortCodes,
                services=sorted(node.services),
            )
        return node_ids[identity]

    root_id = get_node_id(root)

    def add_edge(
        source: str,
        target: str,
        service: RttGbnrServiceData,
        *,
        plan_arr: datetime | None = None,
        act_arr: datetime | None = None,
        plan_dep: datetime | None = None,
        act_dep: datetime | None = None,
    ) -> None:
        service_id = service.get_unique_identity()
        key = (source, target, service_id)
        edge = edges.setdefault(
            key,
            ServiceGraphEdgeData(
                source=source,
                target=target,
                service=service_id,
                plan_arr=None,
                act_arr=None,
                plan_dep=None,
                act_dep=None,
            ),
        )
        if plan_arr is not None:
            edge["plan_arr"] = optional_isoformat(plan_arr)
        if act_arr is not None:
            edge["act_arr"] = optional_isoformat(act_arr)
        if plan_dep is not None:
            edge["plan_dep"] = optional_isoformat(plan_dep)
        if act_dep is not None:
            edge["act_dep"] = optional_isoformat(act_dep)

    visited: set[int] = set()
    while nodes_to_visit:
        node = nodes_to_visit.popleft()
        node_identity = id(node)
        if node_identity in visited:
            continue
        visited.add(node_identity)
        node_id = node_ids[node_identity]

        for parent in node.parents:
            parent_id = get_node_id(parent.node)
            add_edge(
                parent_id,
                node_id,
                parent.service,
                plan_arr=parent.plan_arr,
                act_arr=parent.act_arr,
            )

        for child in node.children:
            child_id = get_node_id(child.node)
            add_edge(
                node_id,
                child_id,
                child.service,
                plan_dep=child.plan_dep,
                act_dep=child.act_dep,
            )

    return ServiceGraphData(
        root=root_id,
        nodes=list(nodes.values()),
        edges=list(edges.values()),
    )

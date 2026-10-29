from tkinter import N
from typing import Optional

from api.pull.train.classes.gbnr.service import (
    RttGbnrAssociatedService,
    RttGbnrServiceData,
    RttGbnrServiceLocation,
)
from api.pull.train.classes.service import RttAssociationType
from api.record.train.tree.node import TrainCallTreeNode

reciprocal_association_types: dict[RttAssociationType, RttAssociationType] = {
    RttAssociationType.JOIN_INTO: RttAssociationType.JOIN_FROM,
    RttAssociationType.JOIN_FROM: RttAssociationType.JOIN_INTO,
    RttAssociationType.DIVIDE_INTO: RttAssociationType.DIVIDE_FROM,
    RttAssociationType.DIVIDE_FROM: RttAssociationType.DIVIDE_INTO,
}
parent_association_types = {
    RttAssociationType.JOIN_FROM,
    RttAssociationType.DIVIDE_FROM,
}


def get_call_tree(
    root_service: RttGbnrServiceData,
    services_dict: dict[str, RttGbnrServiceData],
) -> Optional[TrainCallTreeNode]:
    first_node, _ = _build_service_tree(root_service, set(), services_dict)
    return first_node


def _find_associated_location_index(
    current_service: RttGbnrServiceData,
    associated_service: RttGbnrServiceData,
    association_type: RttAssociationType,
) -> Optional[int]:
    current_unique_identity = current_service.get_unique_identity()
    reciprocal_type = reciprocal_association_types[association_type]
    for index, location in enumerate(associated_service.locations):
        for call_associated_service in location.associatedServices:
            if (
                call_associated_service.get_unique_identity()
                == current_unique_identity
                and call_associated_service.get_association_type()
                == reciprocal_type
            ):
                return index
    return None


def _find_service_location_node(
    tree: TrainCallTreeNode,
    service: RttGbnrServiceData,
    location: RttGbnrServiceLocation,
) -> Optional[TrainCallTreeNode]:
    nodes_to_visit = [tree]
    visited_nodes: set[int] = set()
    while nodes_to_visit:
        node = nodes_to_visit.pop()
        if id(node) in visited_nodes:
            continue
        visited_nodes.add(id(node))
        if node.service is service and node.location is location:
            return node
        nodes_to_visit.extend(node.children)
    return None


def _build_service_tree(
    current_service: RttGbnrServiceData,
    visited_services: set[str],
    services_dict: dict[str, RttGbnrServiceData],
) -> tuple[Optional[TrainCallTreeNode], set[str]]:
    service_key = current_service.get_unique_identity()
    if service_key in visited_services:
        return (None, visited_services)
    visited_services = visited_services | {service_key}
    next_call = None
    for location in reversed(current_service.locations):
        call_node = TrainCallTreeNode(current_service, location)
        for associated_service in location.associatedServices:
            association_type = associated_service.get_association_type()
            if association_type not in reciprocal_association_types:
                continue
            associated_service_key = associated_service.get_unique_identity()
            associated_service_data = services_dict.get(associated_service_key)
            if associated_service_data is None:
                continue
            associated_tree, visited_services = _build_service_tree(
                associated_service_data,
                visited_services,
                services_dict,
            )
            if associated_tree is None:
                continue
            if association_type in parent_association_types:
                joining_call = _find_service_location_node(
                    associated_tree, current_service, location
                )
                if joining_call is None:
                    raise RuntimeError(
                        "Could not find join call in associated service tree"
                    )
                joining_call.children.append(call_node)
                call_node.parents.append(joining_call)
            else:
                call_node.children.extend(associated_tree.children)
                for _, child in associated_tree.children:
                    child.parents.append((location.get_plan_arr(), call_node))
                associated_tree.children.parents.append(call_node)
            if next_call is not None:
                call_node.children.append(next_call)
                next_call.children.append(call_node)
            next_call = call_node
    return next_call, visited_services

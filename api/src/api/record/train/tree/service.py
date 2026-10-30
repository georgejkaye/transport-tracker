from datetime import date
from typing import Optional

from api.pull.train.api import RttApiManager
from api.pull.train.classes.gbnr.service import (
    RttGbnrServiceData,
)
from api.pull.train.classes.location import RttGeographicLocation
from api.pull.train.classes.service import RttAssociationType
from api.pull.train.clients.api import RttApiClient
from api.pull.train.clients.gbnr import RttGbnrClient
from api.record.train.tree.node import (
    TrainCallTreeChildRelation,
    TrainCallTreeNode,
    TrainCallTreeParentRelation,
)

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


def _find_service_location_node(
    tree: TrainCallTreeNode,
    service: RttGbnrServiceData,
    location: RttGeographicLocation,
) -> Optional[TrainCallTreeNode]:
    nodes_to_visit = [tree]
    visited_nodes: set[int] = set()
    while nodes_to_visit:
        node = nodes_to_visit.pop()
        if id(node) in visited_nodes:
            continue
        visited_nodes.add(id(node))
        if (
            service.get_unique_identity() in node.services
            and node.location is location
        ):
            return node
        nodes_to_visit.extend([child.node for child in node.children])
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
    next_call: Optional[TrainCallTreeNode] = None
    call_node: Optional[TrainCallTreeNode] = None
    for location in reversed(current_service.locations):
        call_node = TrainCallTreeNode(
            location.get_geographic_location(),
            set([current_service.get_unique_identity()]),
        )
        parent_relation = TrainCallTreeParentRelation(
            current_service,
            location.get_plan_arr(),
            location.get_act_arr(),
            call_node,
        )
        child_relation = TrainCallTreeChildRelation(
            current_service,
            location.get_plan_dep(),
            location.get_act_dep(),
            call_node,
        )
        for associated_service in location.associatedServices:
            call_node.services.add(associated_service.get_unique_identity())
            association_type = associated_service.get_association_type()
            if association_type not in reciprocal_association_types:
                continue
            associated_service_key = associated_service.get_unique_identity()
            associated_service_data = services_dict.get(associated_service_key)
            if associated_service_data is None:
                continue
            associated_node, visited_services = _build_service_tree(
                associated_service_data,
                visited_services,
                services_dict,
            )
            if associated_node is None:
                continue
            if association_type in parent_association_types:
                call_node = _find_service_location_node(
                    associated_node,
                    current_service,
                    location.get_geographic_location(),
                )
                if call_node is None:
                    raise RuntimeError(
                        "Could not find join call in associated service tree"
                    )

                call_node.children.append(child_relation)
            else:
                call_node = associated_node
        if next_call is not None:
            call_node.children.append(
                TrainCallTreeChildRelation(
                    service,
                    location.get_plan_dep(),
                    location.get_act_dep(),
                    next_call,
                )
            )
            next_call.parents.append(parent_relation)
        next_call = call_node
    return call_node, visited_services


def _get_all_services_from_root_service(
    root_service: RttGbnrServiceData,
) -> dict[str, RttGbnrServiceData]:
    services = {root_service.get_unique_identity(): root_service}
    services_to_visit = [root_service]
    while services_to_visit:
        current_service = services_to_visit.pop(0)
        for location in current_service.locations:
            for associated_service in location.associatedServices:
                service_key = associated_service.get_unique_identity()
                if service_key in services:
                    continue
                associated_service_data = (
                    rtt_gbnr_client.get_service_by_identity_and_departure_date(
                        associated_service.get_identity(),
                        associated_service.get_run_date(),
                    ).service
                )
                services[service_key] = associated_service_data
                services_to_visit.append(associated_service_data)
    return services


def print_node_in_current_service(level: int, node: TrainCallTreeNode):
    indents = "| " * (level + 1)
    print(f"{indents}{node.location.description}")
    for i, child in enumerate(node.children):
        j = len(node.children) - 1 - i
        if j >= 1:
            print_node_in_new_service(level + j, child.node)
        else:
            print_node_in_current_service(level, child.node)


def print_node_in_new_service(level: int, node: TrainCallTreeNode):
    indents = "| " * level
    print(f"{indents}\\")
    print_node_in_current_service(level, node)
    print(f"{indents}*")


if __name__ == "__main__":
    rtt_client = RttApiClient()
    rtt_api_manager = RttApiManager(rtt_client)
    rtt_gbnr_client = RttGbnrClient(rtt_api_manager.get_access_token().token)
    service = rtt_gbnr_client.get_service_by_identity_and_departure_date(
        "G26252", date(2026, 10, 30)
    ).service
    services = _get_all_services_from_root_service(service)
    tree = get_call_tree(service, services)
    if tree is None:
        exit(1)
    print_node_in_new_service(0, tree)

from collections import deque
from datetime import date
from typing import Optional

from api.pull.train.classes.gbnr.service import (
    RttGbnrServiceData,
    RttGbnrServiceLocation,
)
from api.pull.train.classes.service import RttAssociationType
from api.pull.train.clients.gbnr import RttGbnrClient
from api.train.service.graph.classes import (
    ServiceGraphAssociation,
    ServiceGraphBuilderDataKey,
    ServiceGraphChildRelation,
    ServiceGraphNode,
    ServiceGraphParentRelation,
)

reciprocal_association_types: dict[RttAssociationType, RttAssociationType] = {
    RttAssociationType.JOIN_INTO: RttAssociationType.JOIN_FROM,
    RttAssociationType.JOIN_FROM: RttAssociationType.JOIN_INTO,
    RttAssociationType.DIVIDE_INTO: RttAssociationType.DIVIDE_FROM,
    RttAssociationType.DIVIDE_FROM: RttAssociationType.DIVIDE_INTO,
}


def get_service_graph(
    identity: str,
    departure_date: date,
    rtt_gbnr_client: RttGbnrClient,
) -> Optional[ServiceGraphNode]:
    root_service = rtt_gbnr_client.get_service_by_identity_and_departure_date(
        identity, departure_date
    ).service
    services = get_all_services_from_root_service(root_service, rtt_gbnr_client)
    return _build_service_graph(root_service, services)


def get_all_services_from_root_service(
    root_service: RttGbnrServiceData,
    rtt_gbnr_client: RttGbnrClient,
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


def _build_service_graph(
    root_service: RttGbnrServiceData,
    services_dict: dict[str, RttGbnrServiceData],
) -> Optional[ServiceGraphNode]:
    root_key = root_service.get_unique_identity()
    if not root_service.locations:
        return None
    reachable_services, associations = _get_service_associations(
        root_service, services_dict
    )
    raw_graph_nodes = _get_raw_graph_nodes(reachable_services)
    node_representatives = _get_node_representatives(
        raw_graph_nodes, associations, reachable_services
    )
    call_nodes = _resolve_call_nodes(raw_graph_nodes, node_representatives)
    call_nodes_with_relations = _add_node_relations(
        reachable_services, call_nodes
    )
    return call_nodes_with_relations[ServiceGraphBuilderDataKey(root_key, 0)]


def _resolve_call_nodes(
    call_nodes: dict[ServiceGraphBuilderDataKey, ServiceGraphNode],
    representatives_dict: dict[
        ServiceGraphBuilderDataKey, ServiceGraphBuilderDataKey
    ],
) -> dict[ServiceGraphBuilderDataKey, ServiceGraphNode]:
    nodes_by_root: dict[ServiceGraphBuilderDataKey, ServiceGraphNode] = {}
    shared_call_nodes: dict[ServiceGraphBuilderDataKey, ServiceGraphNode] = {}
    for builder_key, node in call_nodes.items():
        representative = representatives_dict[builder_key]
        shared_node = nodes_by_root.get(representative)
        if shared_node is None:
            shared_node = node
            nodes_by_root[representative] = shared_node
        else:
            shared_node.services.update(node.services)
        shared_call_nodes[builder_key] = shared_node
    return shared_call_nodes


def _get_node_representatives(
    raw_graph_nodes: dict[ServiceGraphBuilderDataKey, ServiceGraphNode],
    associations: list[ServiceGraphAssociation],
    reachable_services: dict[str, RttGbnrServiceData],
) -> dict[ServiceGraphBuilderDataKey, ServiceGraphBuilderDataKey]:
    merged_dict: dict[
        ServiceGraphBuilderDataKey, ServiceGraphBuilderDataKey
    ] = {call_key: call_key for call_key in raw_graph_nodes}

    for association in associations:
        associated_key = association.associated_service.get_unique_identity()
        if associated_key not in reachable_services:
            continue
        location = reachable_services[association.service_identity].locations[
            association.location_index
        ]
        associated_location_index = _find_associated_location_index(
            reachable_services[associated_key],
            association.service_identity,
            association.association_type,
            location,
        )
        if associated_location_index is None:
            raise RuntimeError(
                f"Could not find {associated_key} call at "
                f"{location.get_geographic_location().description}"
            )
        first = ServiceGraphBuilderDataKey(
            association.service_identity, association.location_index
        )
        second = ServiceGraphBuilderDataKey(
            associated_key, associated_location_index
        )
        first_representative = _resolve_merged_node(merged_dict, first)
        second_representative = _resolve_merged_node(merged_dict, second)
        if first_representative != second_representative:
            merged_dict[second_representative] = first_representative

    return {
        builder_key: _resolve_merged_node(merged_dict, builder_key)
        for builder_key in merged_dict
    }


def _get_service_associations(
    root_service: RttGbnrServiceData,
    services_dict: dict[str, RttGbnrServiceData],
) -> tuple[
    dict[str, RttGbnrServiceData],
    list[ServiceGraphAssociation],
]:
    reachable_services = {root_service.get_unique_identity(): root_service}
    service_queue = deque([root_service.get_unique_identity()])
    associations: list[ServiceGraphAssociation] = []
    while service_queue:
        service_key = service_queue.popleft()
        service = reachable_services[service_key]
        for location_index, location in enumerate(service.locations):
            for associated_service in location.associatedServices:
                association_type = associated_service.get_association_type()
                if association_type not in reciprocal_association_types:
                    continue
                associated_key = associated_service.get_unique_identity()
                associations.append(
                    ServiceGraphAssociation(
                        service_key,
                        location_index,
                        associated_service,
                        association_type,
                    )
                )
                if associated_key in reachable_services:
                    continue
                associated_service_data = services_dict.get(associated_key)
                if associated_service_data is not None:
                    reachable_services[associated_key] = associated_service_data
                    service_queue.append(associated_key)
    return reachable_services, associations


def _find_associated_location_index(
    service: RttGbnrServiceData,
    associated_service_key: str,
    association_type: RttAssociationType,
    location: RttGbnrServiceLocation,
) -> Optional[int]:
    description = location.get_geographic_location().description
    candidates = [
        index
        for index, service_location in enumerate(service.locations)
        if service_location.get_geographic_location().description == description
    ]
    reciprocal_type = reciprocal_association_types[association_type]
    reciprocal_candidates = [
        index
        for index in candidates
        if any(
            associated.get_unique_identity() == associated_service_key
            and associated.get_association_type() == reciprocal_type
            for associated in service.locations[index].associatedServices
        )
    ]
    if len(reciprocal_candidates) == 1:
        return reciprocal_candidates[0]
    if len(reciprocal_candidates) > 1:
        candidates = reciprocal_candidates
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        return None
    location_codes = location.get_geographic_location().shortCodes
    if location_codes:
        matching_codes = [
            index
            for index in candidates
            if set(location_codes)
            & set(
                service.locations[index].get_geographic_location().shortCodes
                or []
            )
        ]
        if len(matching_codes) == 1:
            return matching_codes[0]
    raise RuntimeError(
        f"Ambiguous {service.get_unique_identity()} calls at {description}"
    )


def _get_raw_graph_nodes(
    services: dict[str, RttGbnrServiceData],
) -> dict[ServiceGraphBuilderDataKey, ServiceGraphNode]:
    call_nodes: dict[ServiceGraphBuilderDataKey, ServiceGraphNode] = {}
    for service_key, service in services.items():
        for location_index, location in enumerate(service.locations):
            call_key = ServiceGraphBuilderDataKey(service_key, location_index)
            service_identities = {service_key}
            service_identities.update(
                associated.get_unique_identity()
                for associated in location.associatedServices
            )
            call_nodes[call_key] = ServiceGraphNode(
                location.get_geographic_location(), service_identities
            )
    return call_nodes


def _resolve_merged_node(
    merged_dict: dict[ServiceGraphBuilderDataKey, ServiceGraphBuilderDataKey],
    builder_key: ServiceGraphBuilderDataKey,
) -> ServiceGraphBuilderDataKey:
    while merged_dict[builder_key] != builder_key:
        builder_key = merged_dict[builder_key]
    return builder_key


def _add_node_relations(
    reachable_services: dict[str, RttGbnrServiceData],
    call_nodes: dict[ServiceGraphBuilderDataKey, ServiceGraphNode],
) -> dict[ServiceGraphBuilderDataKey, ServiceGraphNode]:
    for service_identity, service in reachable_services.items():
        for location_index, location in enumerate(service.locations[:-1]):
            source_node = call_nodes[
                ServiceGraphBuilderDataKey(service_identity, location_index)
            ]
            target_node = call_nodes[
                ServiceGraphBuilderDataKey(service_identity, location_index + 1)
            ]
            source_node.children.append(
                ServiceGraphChildRelation(
                    service,
                    location.get_plan_dep(),
                    location.get_act_dep(),
                    target_node,
                )
            )
            target_location = service.locations[location_index + 1]
            target_node.parents.append(
                ServiceGraphParentRelation(
                    service,
                    target_location.get_plan_arr(),
                    target_location.get_act_arr(),
                    source_node,
                )
            )
    return call_nodes

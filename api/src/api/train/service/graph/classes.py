from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, TypedDict

from api.pull.train.classes.gbnr.service import (
    RttGbnrAssociatedService,
    RttGbnrServiceData,
)
from api.pull.train.classes.location import RttGeographicLocation
from api.pull.train.classes.service import RttAssociationType


@dataclass
class ServiceGraphChildRelation:
    service: RttGbnrServiceData
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    node: "ServiceGraphNode"
    association_type: Optional[RttAssociationType] = None


@dataclass
class ServiceGraphParentRelation:
    service: RttGbnrServiceData
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    node: "ServiceGraphNode"
    association_type: Optional[RttAssociationType] = None


@dataclass
class ServiceGraphNode:
    location: RttGeographicLocation
    services: set[str]
    parents: list[ServiceGraphParentRelation] = field(
        default_factory=lambda: list[ServiceGraphParentRelation]()
    )
    children: list[ServiceGraphChildRelation] = field(
        default_factory=lambda: list[ServiceGraphChildRelation]()
    )


class ServiceGraphNodeData(TypedDict):
    id: str
    location: str | None
    short_codes: list[str] | None
    services: list[str]


class ServiceGraphEdgeData(TypedDict):
    source: str
    target: str
    service: str
    plan_arr: str | None
    act_arr: str | None
    plan_dep: str | None
    act_dep: str | None


class ServiceGraphData(TypedDict):
    root: str
    nodes: list[ServiceGraphNodeData]
    edges: list[ServiceGraphEdgeData]


@dataclass
class ServiceGraphAssociation:
    service_identity: str
    location_index: int
    associated_service: RttGbnrAssociatedService
    association_type: RttAssociationType


@dataclass(frozen=True)
class ServiceGraphBuilderDataKey:
    service_identity: str
    location_index: int

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from api.pull.train.classes.gbnr.service import (
    RttGbnrServiceData,
)
from api.pull.train.classes.location import RttGeographicLocation


@dataclass
class TrainCallTreeChildRelation:
    service: RttGbnrServiceData
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]
    node: "TrainCallTreeNode"


@dataclass
class TrainCallTreeParentRelation:
    service: RttGbnrServiceData
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    node: "TrainCallTreeNode"


@dataclass
class TrainCallTreeNode:
    location: RttGeographicLocation
    services: set[str]
    parents: list[TrainCallTreeParentRelation] = field(
        default_factory=lambda: list[TrainCallTreeParentRelation]()
    )
    children: list[TrainCallTreeChildRelation] = field(
        default_factory=lambda: list[TrainCallTreeChildRelation]()
    )

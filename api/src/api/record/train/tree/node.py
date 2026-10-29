from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from api.pull.train.classes.gbnr.service import (
    RttGbnrServiceData,
    RttGbnrServiceLocation,
)


@dataclass
class TrainCallTreeNodeRelation:
    plan: Optional[datetime]
    act: Optional[datetime]
    node: "TrainCallTreeNode"


@dataclass
class TrainCallTreeNode:
    service: RttGbnrServiceData
    location: RttGbnrServiceLocation
    parents: list[TrainCallTreeNodeRelation] = field(
        default_factory=lambda: list[TrainCallTreeNodeRelation]()
    )
    children: list[TrainCallTreeNodeRelation] = field(
        default_factory=lambda: list[TrainCallTreeNodeRelation]()
    )

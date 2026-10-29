from dataclasses import dataclass, field
from datetime import datetime

from api.pull.train.classes.gbnr.service import (
    RttGbnrServiceData,
    RttGbnrServiceLocation,
)


@dataclass
class TrainCallTreeNode:
    service: RttGbnrServiceData
    location: RttGbnrServiceLocation
    parents: list[tuple[datetime, "TrainCallTreeNode"]] = field(
        default_factory=lambda: list[tuple[datetime, TrainCallTreeNode]]()
    )
    children: list[tuple[datetime, "TrainCallTreeNode"]] = field(
        default_factory=lambda: list[tuple[datetime, TrainCallTreeNode]]()
    )

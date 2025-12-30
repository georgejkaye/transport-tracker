from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from api.db.types.user.train.leg import TransportUserTrainLegOutData
from api.db.types.user.train.operator import (
    TransportUserTrainOperatorHighOutData,
)
from api.db.types.user.train.vehicle import (
    TransportUserTrainClassHighOutData,
    TransportUserTrainUnitHighOutData,
)


@dataclass
class TrainStats:
    leg_count: int
    distance: Decimal
    duration: timedelta
    delay: int
    longest_legs: list[TransportUserTrainLegOutData]
    shortest_legs: list[TransportUserTrainLegOutData]
    operator_count: int
    top_operators: list[TransportUserTrainOperatorHighOutData]
    class_count: int
    top_classes: list[TransportUserTrainClassHighOutData]
    unit_count: int
    top_units: list[TransportUserTrainUnitHighOutData]
    longest_delay: int
    shortest_delay: int

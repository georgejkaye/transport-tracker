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
    total_distance: Decimal
    longest_distance: Decimal
    longest_distance_legs: list[TransportUserTrainLegOutData]
    shortest_distance: Decimal
    shortest_distance_legs: list[TransportUserTrainLegOutData]
    total_duration: timedelta
    longest_duration: timedelta
    longest_duration_legs: list[TransportUserTrainLegOutData]
    shortest_duration: timedelta
    shortest_duration_legs: list[TransportUserTrainLegOutData]
    total_delay: int
    longest_delay: int
    longest_delay_legs: list[TransportUserTrainLegOutData]
    shortest_delay: int
    shortest_delay_legs: list[TransportUserTrainLegOutData]
    operator_count: int
    top_operators: list[TransportUserTrainOperatorHighOutData]
    class_count: int
    top_classes: list[TransportUserTrainClassHighOutData]
    unit_count: int
    top_units: list[TransportUserTrainUnitHighOutData]

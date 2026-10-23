from dataclasses import dataclass

from api.db.types.train.operator import TrainOperatorDetailsOutData


@dataclass
class OperatorBrandLookup:
    operators: dict[int, TrainOperatorDetailsOutData]
    brands: dict[int, TrainOperatorDetailsOutData]

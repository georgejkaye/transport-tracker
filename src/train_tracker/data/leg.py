from dataclasses import dataclass
from decimal import Decimal

from train_tracker.data.services import TrainService
from train_tracker.data.stock import Stock


@dataclass
class Leg:
    service: TrainService
    origin_station: str
    destination_station: str
    mileage: Decimal
    stock: Stock

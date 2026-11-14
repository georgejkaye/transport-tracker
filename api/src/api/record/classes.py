from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from api.data.bus.pages.journey.classes import BustimesJourneyVehicle
from api.db.types.bus.journey import BusCallInData
from api.db.types.bus.operator import BusOperatorDetails
from api.db.types.bus.service import BusServiceDetails
from api.db.types.train.leg import TrainLegCallInData


@dataclass
class BustimesJourneyData:
    calls: list[BusCallInData]
    board_call_index: int
    operator: BusOperatorDetails
    service: BusServiceDetails
    vehicle: Optional[BustimesJourneyVehicle]


@dataclass
class StockReport:
    class_no: Optional[int]
    subclass_no: Optional[int]
    stock_no: Optional[int]
    cars: Optional[int]


@dataclass
class StockSegment:
    stock_reports: list[StockReport]
    service_uid: str
    run_date: datetime
    start_call: TrainLegCallInData
    end_call: TrainLegCallInData
    mileage: Optional[Decimal]

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

from api.pull.train.classes.schedule import RttScheduleOperator


@dataclass
class RttGbnrScheduleMetadata:
    uniqueIdentity: Optional[str] = None
    namespace: Optional[str] = None
    identity: Optional[str] = None
    departureDate: Optional[str] = None
    operator: Optional[RttScheduleOperator] = None
    modeType: Optional[str] = None
    inPassengerService: Optional[bool] = None
    allocations: Optional[dict[str, Any]] = None
    trainReportingIdentity: Optional[str] = None
    stpIndicator: Optional[str] = None
    runsAsRequired: Optional[bool] = None


class HasGbnrScheduleMetadata(ABC):
    @abstractmethod
    def get_schedule_metadata(self) -> RttGbnrScheduleMetadata:
        pass

    def get_identity(self) -> str:
        if (identity := self.get_schedule_metadata().identity) is None:
            raise RuntimeError("scheduleMetadata.identity field missing")
        return identity

    def get_run_date(self) -> date:
        if (run_date := self.get_schedule_metadata().departureDate) is None:
            raise RuntimeError("scheduleMetadata.identity field missing")
        return date.fromisoformat(run_date)

    def get_headcode(self) -> str:
        if (
            headcode := self.get_schedule_metadata().trainReportingIdentity
        ) is None:
            raise RuntimeError("scheduleMetadata.headcode field missing")
        return headcode

    def get_operator(self) -> RttScheduleOperator:
        if (operator := self.get_schedule_metadata().operator) is None:
            raise RuntimeError("scheduleMetadata.operator field missing")
        return operator

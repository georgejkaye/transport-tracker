from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from api.pull.train.classes.temporal import RttIndividualTemporalData
from api.utils.times import make_timezone_aware


@dataclass
class RttGeographicLocation:
    namespace: Optional[str] = None
    description: Optional[str] = None
    shortCodes: Optional[list[str]] = None
    longCodes: Optional[list[str]] = None


class HasGeographicLocation(ABC):
    @abstractmethod
    def get_geographic_location(self) -> RttGeographicLocation:
        pass

    def get_description(self) -> str:
        geographic_location = self.get_geographic_location()
        if (description := geographic_location.description) is None:
            raise RuntimeError("description missing from geographic location")
        return description


@dataclass
class RttLocationReason:
    type: Optional[str] = None
    code: Optional[str] = None
    system: Optional[str] = None
    shortText: Optional[str] = None
    longText: Optional[str] = None


@dataclass
class RttLocationTemporalData:
    arrival: Optional[RttIndividualTemporalData] = None
    departure: Optional[RttIndividualTemporalData] = None
    pass_: Optional[RttIndividualTemporalData] = None
    scheduledCallType: Optional[str] = None
    realtimeCallType: Optional[str] = None
    displayAs: Optional[str] = None
    status: Optional[str] = None
    isInterpolated: Optional[bool] = None


class HasLocationTemporalData(ABC):
    @abstractmethod
    def get_temporal_data(self) -> RttLocationTemporalData:
        pass

    def _get_datetime(
        self, data: Optional[RttIndividualTemporalData], actual: bool = False
    ) -> Optional[datetime]:
        if data is None:
            return None
        time_string = data.realtimeActual if actual else data.scheduleAdvertised
        return (
            make_timezone_aware(datetime.fromisoformat(time_string))
            if time_string is not None
            else None
        )

    def get_plan_arr(self) -> Optional[datetime]:
        arrival = self.get_temporal_data().arrival
        return self._get_datetime(arrival)

    def get_plan_dep(self) -> Optional[datetime]:
        departure = self.get_temporal_data().departure
        return self._get_datetime(departure)

    def get_act_arr(self) -> Optional[datetime]:
        arrival = self.get_temporal_data().arrival
        return self._get_datetime(arrival, actual=True)

    def get_act_dep(self) -> Optional[datetime]:
        departure = self.get_temporal_data().departure
        return self._get_datetime(departure, actual=True)


@dataclass
class RttLocationPair(HasGeographicLocation):
    location: Optional[RttGeographicLocation] = None
    temporalData: Optional[RttIndividualTemporalData] = None

    def get_geographic_location(self) -> RttGeographicLocation:
        if (location := self.location) is None:
            raise RuntimeError("location tag missing from location pair")
        return location

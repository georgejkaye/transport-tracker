from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from api.pull.train.classes.gbnr.schedule import (
    HasGbnrScheduleMetadata,
    RttGbnrScheduleMetadata,
)
from api.pull.train.classes.location import (
    HasLocationTemporalData,
    RttGeographicLocation,
    RttLocationPair,
    RttLocationReason,
    RttLocationTemporalData,
)
from api.pull.train.classes.planact import RttPlannedActualData
from api.pull.train.classes.schedule import RttScheduleOperator
from api.pull.train.classes.system import RttSystemStatus
from api.pull.train.classes.temporal import (
    RttIndividualTemporalData,
)


@dataclass
class RttGbnrLocationQuery:
    location: Optional[RttGeographicLocation] = None
    timeFrom: Optional[str] = None
    timeTo: Optional[str] = None
    stpFilter: Optional["RttGbnrStpFilter"] = None


@dataclass
class RttGbnrStpFilter:
    WTT: Optional[bool] = None
    VAR: Optional[bool] = None
    STP: Optional[bool] = None
    CAN: Optional[bool] = None


@dataclass
class RttGbnrLocationAllowances:
    engineering: Optional[int] = None
    pathing: Optional[int] = None
    performance: Optional[int] = None


@dataclass
class RttGbnrLocationMetadata:
    platform: Optional[RttPlannedActualData] = None
    line: Optional[RttPlannedActualData] = None
    path: Optional[RttPlannedActualData] = None
    numberOfVehicles: Optional[int] = None
    allocationIndex: Optional[int] = None
    isRequestStop: Optional[bool] = None
    stockBranding: Optional[str] = None
    allowances: Optional[RttGbnrLocationAllowances] = None


class HasGbnrLocationMetadata(ABC):
    @abstractmethod
    def get_location_metadata(self) -> RttGbnrLocationMetadata:
        pass

    def get_platform(self) -> Optional[str]:
        location_metadata = self.get_location_metadata()
        platform_data = location_metadata.platform
        if platform_data is None:
            return None
        if platform_data.actual is not None:
            return platform_data.actual
        return platform_data.planned


@dataclass
class RttGbnrLocationService(HasLocationTemporalData, HasGbnrScheduleMetadata):
    reasons: list[RttLocationReason]
    origin: list[RttLocationPair]
    destination: list[RttLocationPair]
    temporalData: Optional[RttLocationTemporalData] = None
    locationMetadata: Optional[RttGbnrLocationMetadata] = None
    scheduleMetadata: Optional[RttGbnrScheduleMetadata] = None

    def get_temporal_data(self) -> RttLocationTemporalData:
        if self.temporalData is None:
            raise RuntimeError("temporalData is missing from location service")
        return self.temporalData

    def get_schedule_metadata(self) -> RttGbnrScheduleMetadata:
        if self.scheduleMetadata is None:
            raise RuntimeError(
                "scheduleMetadata field missing in location service"
            )
        return self.scheduleMetadata


@dataclass
class RttGbnrLocationResponse:
    systemStatus: RttSystemStatus
    query: RttGbnrLocationQuery
    reasons: list[RttLocationReason]
    services: list[RttGbnrLocationService]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RttGbnrLocationResponse":
        query_data = data["query"]
        return RttGbnrLocationResponse(
            systemStatus=RttSystemStatus(**data["systemStatus"]),
            query=RttGbnrLocationQuery(
                location=(
                    RttGeographicLocation(**query_data["location"])
                    if query_data.get("location") is not None
                    else None
                ),
                timeFrom=query_data.get("timeFrom"),
                timeTo=query_data.get("timeTo"),
                stpFilter=(
                    RttGbnrStpFilter(**query_data["stpFilter"])
                    if query_data.get("stpFilter") is not None
                    else None
                ),
            ),
            reasons=[RttLocationReason(**reason) for reason in data["reasons"]],
            services=[
                _location_service_from_dict(service)
                for service in data["services"]
            ],
        )


def _individual_temporal_data_from_dict(
    data: Optional[dict[str, Any]],
) -> Optional[RttIndividualTemporalData]:
    return RttIndividualTemporalData(**data) if data is not None else None


def _location_service_from_dict(data: dict[str, Any]) -> RttGbnrLocationService:
    temporal_data = data.get("temporalData")
    if temporal_data is not None:
        temporal_data = RttLocationTemporalData(
            arrival=_individual_temporal_data_from_dict(
                temporal_data.get("arrival")
            ),
            departure=_individual_temporal_data_from_dict(
                temporal_data.get("departure")
            ),
            pass_=_individual_temporal_data_from_dict(
                temporal_data.get("pass")
            ),
            scheduledCallType=temporal_data.get("scheduledCallType"),
            realtimeCallType=temporal_data.get("realtimeCallType"),
            displayAs=temporal_data.get("displayAs"),
            status=temporal_data.get("status"),
            isInterpolated=temporal_data.get("isInterpolated"),
        )

    location_metadata = data.get("locationMetadata")
    if location_metadata is not None:
        location_metadata = RttGbnrLocationMetadata(
            platform=(
                RttPlannedActualData(**location_metadata["platform"])
                if location_metadata.get("platform") is not None
                else None
            ),
            line=(
                RttPlannedActualData(**location_metadata["line"])
                if location_metadata.get("line") is not None
                else None
            ),
            path=(
                RttPlannedActualData(**location_metadata["path"])
                if location_metadata.get("path") is not None
                else None
            ),
            numberOfVehicles=location_metadata.get("numberOfVehicles"),
            allocationIndex=location_metadata.get("allocationIndex"),
            isRequestStop=location_metadata.get("isRequestStop"),
            stockBranding=location_metadata.get("stockBranding"),
            allowances=(
                RttGbnrLocationAllowances(**location_metadata["allowances"])
                if location_metadata.get("allowances") is not None
                else None
            ),
        )

    schedule_metadata = data.get("scheduleMetadata")
    if schedule_metadata is not None:
        operator = schedule_metadata.get("operator")
        schedule_metadata = RttGbnrScheduleMetadata(
            uniqueIdentity=schedule_metadata.get("uniqueIdentity"),
            namespace=schedule_metadata.get("namespace"),
            identity=schedule_metadata.get("identity"),
            departureDate=schedule_metadata.get("departureDate"),
            operator=(
                RttScheduleOperator(**operator)
                if operator is not None
                else None
            ),
            modeType=schedule_metadata.get("modeType"),
            inPassengerService=schedule_metadata.get("inPassengerService"),
            allocations=schedule_metadata.get("allocations"),
            trainReportingIdentity=schedule_metadata.get(
                "trainReportingIdentity"
            ),
            stpIndicator=schedule_metadata.get("stpIndicator"),
            runsAsRequired=schedule_metadata.get("runsAsRequired"),
        )

    return RttGbnrLocationService(
        temporalData=temporal_data,
        locationMetadata=location_metadata,
        reasons=[
            RttLocationReason(**reason) for reason in data.get("reasons", [])
        ],
        origin=[
            RttLocationPair(
                location=(
                    RttGeographicLocation(**pair["location"])
                    if pair.get("location") is not None
                    else None
                ),
                temporalData=_individual_temporal_data_from_dict(
                    pair.get("temporalData")
                ),
            )
            for pair in data.get("origin", [])
        ],
        destination=[
            RttLocationPair(
                location=(
                    RttGeographicLocation(**pair["location"])
                    if pair.get("location") is not None
                    else None
                ),
                temporalData=_individual_temporal_data_from_dict(
                    pair.get("temporalData")
                ),
            )
            for pair in data.get("destination", [])
        ],
        scheduleMetadata=schedule_metadata,
    )

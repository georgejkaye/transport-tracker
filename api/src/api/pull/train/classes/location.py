from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class RttSystemStatus:
    realtimeNetworkRail: Optional[str] = None
    rttCore: Optional[str] = None


@dataclass
class RttGeographicLocation:
    namespace: Optional[str] = None
    description: Optional[str] = None
    shortCodes: Optional[list[str]] = None
    longCodes: Optional[list[str]] = None


@dataclass
class RttLocationQuery:
    location: Optional[RttGeographicLocation] = None
    timeFrom: Optional[str] = None
    timeTo: Optional[str] = None


@dataclass
class RttLocationReason:
    type: Optional[str] = None
    code: Optional[str] = None
    system: Optional[str] = None
    shortText: Optional[str] = None
    longText: Optional[str] = None


@dataclass
class RttIndividualTemporalData:
    scheduleInternal: Optional[str] = None
    scheduleAdvertised: Optional[str] = None
    realtimeForecast: Optional[str] = None
    realtimeEstimate: Optional[str] = None
    realtimeNoReport: Optional[bool] = None
    realtimeActual: Optional[str] = None
    realtimeInternalLateness: Optional[int] = None
    realtimeAdvertisedLateness: Optional[int] = None
    isCancelled: Optional[bool] = None
    cancellationReasonCode: Optional[str] = None


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


@dataclass
class RttPlannedActualData:
    planned: Optional[str] = None
    forecast: Optional[str] = None
    actual: Optional[str] = None


@dataclass
class RttLocationMetadata:
    platform: Optional[RttPlannedActualData] = None
    line: Optional[RttPlannedActualData] = None
    path: Optional[RttPlannedActualData] = None
    numberOfVehicles: Optional[int] = None
    allocationIndex: Optional[int] = None
    isRequestStop: Optional[bool] = None


@dataclass
class RttLocationPair:
    location: Optional[RttGeographicLocation] = None
    temporalData: Optional[RttIndividualTemporalData] = None


@dataclass
class RttScheduleOperator:
    code: Optional[str] = None
    name: Optional[str] = None


@dataclass
class RttScheduleMetadata:
    uniqueIdentity: Optional[str] = None
    namespace: Optional[str] = None
    identity: Optional[str] = None
    departureDate: Optional[str] = None
    operator: Optional[RttScheduleOperator] = None
    modeType: Optional[str] = None
    inPassengerService: Optional[bool] = None


@dataclass
class RttLocationService:
    reasons: list[RttLocationReason]
    origin: list[RttLocationPair]
    destination: list[RttLocationPair]
    temporalData: Optional[RttLocationTemporalData] = None
    locationMetadata: Optional[RttLocationMetadata] = None
    scheduleMetadata: Optional[RttScheduleMetadata] = None


@dataclass
class RttLocationResponse:
    systemStatus: RttSystemStatus
    query: RttLocationQuery
    reasons: list[RttLocationReason]
    services: list[RttLocationService]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RttLocationResponse":
        query_data = data["query"]
        return RttLocationResponse(
            systemStatus=RttSystemStatus(**data["systemStatus"]),
            query=RttLocationQuery(
                location=(
                    RttGeographicLocation(**query_data["location"])
                    if query_data.get("location") is not None
                    else None
                ),
                timeFrom=query_data.get("timeFrom"),
                timeTo=query_data.get("timeTo"),
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


def _location_service_from_dict(data: dict[str, Any]) -> RttLocationService:
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
        location_metadata = RttLocationMetadata(
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
        )

    schedule_metadata = data.get("scheduleMetadata")
    if schedule_metadata is not None:
        operator = schedule_metadata.get("operator")
        schedule_metadata = RttScheduleMetadata(
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
        )

    return RttLocationService(
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

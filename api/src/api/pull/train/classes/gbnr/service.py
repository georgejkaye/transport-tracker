from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

from api.pull.train.classes.gbnr.location import (
    HasGbnrLocationMetadata,
    RttGbnrLocationAllowances,
    RttGbnrLocationMetadata,
)
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
from api.pull.train.classes.service import (
    RttAssociationData,
    RttAssociationType,
    RttServiceQuery,
)
from api.pull.train.classes.system import RttSystemStatus
from api.pull.train.classes.temporal import (
    RttIndividualTemporalData,
)


@dataclass
class RttGbnrAssociatedService(HasGbnrScheduleMetadata):
    associationData: Optional[RttAssociationData] = None
    scheduleMetadata: Optional[RttGbnrScheduleMetadata] = None

    def get_schedule_metadata(self) -> RttGbnrScheduleMetadata:
        if self.scheduleMetadata is None:
            raise RuntimeError(
                "scheduleMetadata field missing in associated service"
            )
        return self.scheduleMetadata

    def get_association_type(self) -> RttAssociationType:
        if self.associationData is None:
            raise RuntimeError(
                "associationData field missing in associated service"
            )
        if self.associationData.associationType is None:
            raise RuntimeError(
                "associationData.associationType field missing in associated service"
            )
        return self.associationData.associationType


@dataclass
class RttGbnrServiceLocation(HasLocationTemporalData, HasGbnrLocationMetadata):
    temporalData: Optional[RttLocationTemporalData] = None
    locationMetadata: Optional[RttGbnrLocationMetadata] = None
    location: Optional[RttGeographicLocation] = None
    associatedServices: list[RttGbnrAssociatedService] = field(
        default_factory=lambda: list[RttGbnrAssociatedService]()
    )

    def get_temporal_data(self) -> RttLocationTemporalData:
        if self.temporalData is None:
            raise RuntimeError("temporalData missing from service location")
        return self.temporalData

    def get_location_metadata(self) -> RttGbnrLocationMetadata:
        if self.locationMetadata is None:
            raise RuntimeError("locationData missing from service location")
        return self.locationMetadata

    def get_crs(self) -> str:
        if self.location is None:
            raise RuntimeError("location field missing from service location")
        if (
            self.location.shortCodes is None
            or len(self.location.shortCodes) == 0
        ):
            raise RuntimeError(
                "location.shortCodes field missing from service location"
            )
        return self.location.shortCodes[0]

    def get_description(self) -> str:
        if self.location is None:
            raise RuntimeError("location field missing from service location")
        if self.location.description is None:
            raise RuntimeError(
                "location.description field missing from service location"
            )
        return self.location.description


@dataclass
class RttGbnrComponentVehicle:
    identity: Optional[str] = None
    isPassengerVehicle: Optional[bool] = None
    isLocomotive: Optional[bool] = None
    index: Optional[int] = None


@dataclass
class RttGbnrAllocationItem:
    stockType: Optional[str] = None
    identity: Optional[str] = None
    inReverse: Optional[bool] = None
    identitySuppressed: Optional[bool] = None
    numberOfVehicles: Optional[int] = None
    componentVehicles: list[RttGbnrComponentVehicle] = field(
        default_factory=lambda: list[RttGbnrComponentVehicle]()
    )


@dataclass
class RttGbnrKnowYourTrainVehicle:
    graphic: Optional[str] = None
    isPassengerVehicle: Optional[bool] = None
    coachLetter: Optional[str] = None
    individualFacilities: Optional[list[str]] = None


@dataclass
class RttGbnrKnowYourTrainGroup:
    identity: Optional[str] = None
    groupFacilities: Optional[list[str]] = None
    vehicles: list[RttGbnrKnowYourTrainVehicle] = field(
        default_factory=lambda: list[RttGbnrKnowYourTrainVehicle]()
    )


@dataclass
class RttGbnrKnowYourTrainData:
    stockBranding: Optional[str] = None
    commonFacilities: Optional[list[str]] = None
    data: list[RttGbnrKnowYourTrainGroup] = field(
        default_factory=lambda: list[RttGbnrKnowYourTrainGroup]()
    )


@dataclass
class RttGbnrAllocation:
    allocationIndex: Optional[int] = None
    leadingClass: Optional[str] = None
    passengerVehicles: Optional[int] = None
    allocationItems: list[RttGbnrAllocationItem] = field(
        default_factory=lambda: list[RttGbnrAllocationItem]()
    )
    knowYourTrainData: Optional[RttGbnrKnowYourTrainData] = None


@dataclass
class RttGbnrServiceData(HasGbnrScheduleMetadata):
    scheduleMetadata: Optional[RttGbnrScheduleMetadata] = None
    locations: list[RttGbnrServiceLocation] = field(
        default_factory=lambda: list[RttGbnrServiceLocation]()
    )
    allocationData: Optional[list[RttGbnrAllocation]] = None
    origin: list[RttLocationPair] = field(
        default_factory=lambda: list[RttLocationPair]()
    )
    destination: list[RttLocationPair] = field(
        default_factory=lambda: list[RttLocationPair]()
    )
    reasons: list[RttLocationReason] = field(
        default_factory=lambda: list[RttLocationReason]()
    )

    def get_schedule_metadata(self) -> RttGbnrScheduleMetadata:
        if self.scheduleMetadata is None:
            raise RuntimeError("scheduleMetadata field missing in service")
        return self.scheduleMetadata

    def get_run_date(self) -> date:
        if self.scheduleMetadata is None:
            raise RuntimeError("scheduleMetadata field is missing from service")
        if self.scheduleMetadata.departureDate is None:
            raise RuntimeError(
                "scheduleMetadata.departureDate field is missing from service"
            )
        return date.fromisoformat(self.scheduleMetadata.departureDate)

    def get_identity(self) -> str:
        if self.scheduleMetadata is None:
            raise RuntimeError("scheduleMetadata field is missing from service")
        if self.scheduleMetadata.identity is None:
            raise RuntimeError(
                "scheduleMetadata.identity field is missing from service"
            )
        return self.scheduleMetadata.identity


@dataclass
class RttGbnrServiceResponse:
    systemStatus: RttSystemStatus
    query: RttServiceQuery
    service: RttGbnrServiceData

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RttGbnrServiceResponse":
        query_data = data["query"]
        return cls(
            systemStatus=RttSystemStatus(**data["systemStatus"]),
            query=RttServiceQuery(
                uniqueIdentity=query_data.get("uniqueIdentity")
            ),
            service=_service_data_from_dict(data["service"]),
        )


def _individual_temporal_data_from_dict(
    data: Optional[dict[str, Any]],
) -> Optional[RttIndividualTemporalData]:
    return RttIndividualTemporalData(**data) if data is not None else None


def _location_temporal_data_from_dict(
    data: Optional[dict[str, Any]],
) -> Optional[RttLocationTemporalData]:
    if data is None:
        return None
    return RttLocationTemporalData(
        arrival=_individual_temporal_data_from_dict(data.get("arrival")),
        departure=_individual_temporal_data_from_dict(data.get("departure")),
        pass_=_individual_temporal_data_from_dict(data.get("pass")),
        scheduledCallType=data.get("scheduledCallType"),
        realtimeCallType=data.get("realtimeCallType"),
        displayAs=data.get("displayAs"),
        status=data.get("status"),
        isInterpolated=data.get("isInterpolated"),
    )


def _location_metadata_from_dict(
    data: Optional[dict[str, Any]],
) -> Optional[RttGbnrLocationMetadata]:
    if data is None:
        return None
    return RttGbnrLocationMetadata(
        platform=(
            RttPlannedActualData(**data["platform"])
            if data.get("platform") is not None
            else None
        ),
        line=(
            RttPlannedActualData(**data["line"])
            if data.get("line") is not None
            else None
        ),
        path=(
            RttPlannedActualData(**data["path"])
            if data.get("path") is not None
            else None
        ),
        numberOfVehicles=data.get("numberOfVehicles"),
        allocationIndex=data.get("allocationIndex"),
        isRequestStop=data.get("isRequestStop"),
        stockBranding=data.get("stockBranding"),
        allowances=(
            RttGbnrLocationAllowances(**data["allowances"])
            if data.get("allowances") is not None
            else None
        ),
    )


def _schedule_metadata_from_dict(
    data: Optional[dict[str, Any]],
) -> Optional[RttGbnrScheduleMetadata]:
    if data is None:
        return None
    operator = data.get("operator")
    return RttGbnrScheduleMetadata(
        uniqueIdentity=data.get("uniqueIdentity"),
        namespace=data.get("namespace"),
        identity=data.get("identity"),
        departureDate=data.get("departureDate"),
        operator=(
            RttScheduleOperator(**operator) if operator is not None else None
        ),
        modeType=data.get("modeType"),
        inPassengerService=data.get("inPassengerService"),
        allocations=data.get("allocations"),
        trainReportingIdentity=data.get("trainReportingIdentity"),
        stpIndicator=data.get("stpIndicator"),
        runsAsRequired=data.get("runsAsRequired"),
    )


def _location_pair_from_dict(data: dict[str, Any]) -> RttLocationPair:
    location = data.get("location")
    return RttLocationPair(
        location=(
            RttGeographicLocation(**location) if location is not None else None
        ),
        temporalData=_individual_temporal_data_from_dict(
            data.get("temporalData")
        ),
    )


def _service_location_from_dict(
    data: dict[str, Any],
) -> RttGbnrServiceLocation:
    return RttGbnrServiceLocation(
        temporalData=_location_temporal_data_from_dict(
            data.get("temporalData")
        ),
        locationMetadata=_location_metadata_from_dict(
            data.get("locationMetadata")
        ),
        location=(
            RttGeographicLocation(**data["location"])
            if data.get("location") is not None
            else None
        ),
        associatedServices=[
            RttGbnrAssociatedService(
                associationData=(
                    RttAssociationData(
                        associationType=(
                            RttAssociationType(
                                service["associationData"]["associationType"]
                            )
                            if service["associationData"].get("associationType")
                            is not None
                            else None
                        ),
                        isPublic=service["associationData"].get("isPublic"),
                    )
                    if service.get("associationData") is not None
                    else None
                ),
                scheduleMetadata=_schedule_metadata_from_dict(
                    service.get("scheduleMetadata")
                ),
            )
            for service in data.get("associatedServices", [])
        ],
    )


def _allocation_item_from_dict(data: dict[str, Any]) -> RttGbnrAllocationItem:
    return RttGbnrAllocationItem(
        stockType=data.get("stockType"),
        identity=data.get("identity"),
        inReverse=data.get("inReverse"),
        identitySuppressed=data.get("identitySuppressed"),
        numberOfVehicles=data.get("numberOfVehicles"),
        componentVehicles=[
            RttGbnrComponentVehicle(**vehicle)
            for vehicle in data.get("componentVehicles", [])
        ],
    )


def _know_your_train_data_from_dict(
    data: Optional[dict[str, Any]],
) -> Optional[RttGbnrKnowYourTrainData]:
    if data is None:
        return None
    return RttGbnrKnowYourTrainData(
        stockBranding=data.get("stockBranding"),
        commonFacilities=data.get("commonFacilities"),
        data=[
            RttGbnrKnowYourTrainGroup(
                identity=group.get("identity"),
                groupFacilities=group.get("groupFacilities"),
                vehicles=[
                    RttGbnrKnowYourTrainVehicle(**vehicle)
                    for vehicle in group.get("vehicles", [])
                ],
            )
            for group in data.get("data", [])
        ],
    )


def _allocation_from_dict(data: dict[str, Any]) -> RttGbnrAllocation:
    return RttGbnrAllocation(
        allocationIndex=data.get("allocationIndex"),
        leadingClass=data.get("leadingClass"),
        passengerVehicles=data.get("passengerVehicles"),
        allocationItems=[
            _allocation_item_from_dict(item)
            for item in data.get("allocationItems", [])
        ],
        knowYourTrainData=_know_your_train_data_from_dict(
            data.get("knowYourTrainData")
        ),
    )


def _service_data_from_dict(data: dict[str, Any]) -> RttGbnrServiceData:
    allocation_data = data.get("allocationData")
    return RttGbnrServiceData(
        scheduleMetadata=_schedule_metadata_from_dict(
            data.get("scheduleMetadata")
        ),
        locations=[
            _service_location_from_dict(location)
            for location in data.get("locations", [])
        ],
        allocationData=(
            [
                _allocation_from_dict(allocation)
                for allocation in allocation_data
            ]
            if allocation_data is not None
            else None
        ),
        origin=[
            _location_pair_from_dict(location)
            for location in data.get("origin", [])
        ],
        destination=[
            _location_pair_from_dict(location)
            for location in data.get("destination", [])
        ],
        reasons=[
            RttLocationReason(**reason) for reason in data.get("reasons", [])
        ],
    )

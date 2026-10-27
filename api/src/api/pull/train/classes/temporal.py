from dataclasses import dataclass
from typing import Optional


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

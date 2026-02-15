from dataclasses import dataclass

from api.db.types.user.user import (
    TransportUserDetailsTrainLegOutData,
    TransportUserDetailsTrainStationOutData,
    TransportUserTrainOperatorStats,
)


@dataclass
class UserTrainStats:
    leg_stats: TransportUserDetailsTrainLegOutData
    station_stats: TransportUserDetailsTrainStationOutData
    operator_stats: TransportUserTrainOperatorStats


@dataclass
class UserTrainYearStats:
    year: int
    leg_stats: TransportUserDetailsTrainLegOutData
    station_stats: TransportUserDetailsTrainStationOutData
    operator_stats: TransportUserTrainOperatorStats


@dataclass
class UserTrainAllStats:
    overall_stats: UserTrainStats
    year_stats: list[UserTrainYearStats]

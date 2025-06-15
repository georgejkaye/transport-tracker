from datetime import datetime
from decimal import Decimal
from typing import Optional


DbTrainServiceInData = tuple[
    str, datetime, str, str, Optional[str], Optional[str]
]

DbTrainServiceEndpointInData = tuple[str, datetime, str, bool]

DbTrainCallInData = tuple[
    str,
    datetime,
    str,
    Optional[str],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[Decimal],
]

DbTrainAssociatedServiceInData = tuple[
    str,
    datetime,
    str,
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    str,
    datetime,
    str,
]

DbTrainLegCallInData = tuple[
    str,
    Optional[str],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[str],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[Decimal],
]

DbTrainStockSegmentInData = tuple[
    Optional[int],
    Optional[int],
    Optional[int],
    Optional[int],
    str,
    datetime,
    str,
    Optional[datetime],
    Optional[datetime],
    str,
    datetime,
    str,
    Optional[datetime],
    Optional[datetime],
]

DbTrainLegInData = tuple[
    int,
    list[DbTrainServiceInData],
    list[DbTrainServiceEndpointInData],
    list[DbTrainCallInData],
    list[DbTrainAssociatedServiceInData],
    list[DbTrainLegCallInData],
    Decimal,
    list[DbTrainStockSegmentInData],
]

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RttAssociationType(str, Enum):
    JOIN_FROM = "JOIN_FROM"
    JOIN_INTO = "JOIN_INTO"
    DIVIDE_INTO = "DIVIDE_INTO"
    DIVIDE_FROM = "DIVIDE_FROM"
    FORM_INTO = "FORM_INTO"
    FORM_FROM = "FORM_FROM"


def get_rtt_association_type_db_int(
    association_type: RttAssociationType,
) -> int:
    match association_type:
        case RttAssociationType.JOIN_FROM:
            return 4
        case RttAssociationType.JOIN_INTO:
            return 3
        case RttAssociationType.DIVIDE_INTO:
            return 1
        case RttAssociationType.DIVIDE_FROM:
            return 2
        case _:
            raise RuntimeError(
                f"No integer associated with association_type {association_type}"
            )


@dataclass
class RttAssociationData:
    associationType: Optional[RttAssociationType] = None
    isPublic: Optional[bool] = None


@dataclass
class RttServiceQuery:
    uniqueIdentity: Optional[str] = None

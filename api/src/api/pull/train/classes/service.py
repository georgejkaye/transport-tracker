from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RttAssociationType(str, Enum):
    # this service is joined by this associated service
    JOIN_FROM = "JOIN_FROM"
    # this service joins the associated service
    JOIN_INTO = "JOIN_INTO"
    # service divides from this to the associated service
    DIVIDE_INTO = "DIVIDE_INTO"
    # the associated service divides to form this service
    DIVIDE_FROM = "DIVIDE_FROM"
    # this service froms this associated service
    FORM_INTO = "FORM_INTO"
    # this service is formed by this associated service
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

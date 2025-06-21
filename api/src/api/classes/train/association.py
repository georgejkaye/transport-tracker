from enum import Enum
from typing import Optional


AssociationType = Enum(
    "AssociationType",
    ["THIS_JOINS", "OTHER_JOINS", "THIS_DIVIDES", "OTHER_DIVIDES"],
)


def string_of_association_type(at: AssociationType) -> str:
    match at:
        case AssociationType.THIS_JOINS:
            return "THIS_JOINS"
        case AssociationType.OTHER_JOINS:
            return "OTHER_JOINS"
        case AssociationType.THIS_DIVIDES:
            return "THIS_DIVIDES"
        case AssociationType.OTHER_DIVIDES:
            return "OTHER_DIVIDES"


def int_of_association_type(at: AssociationType) -> int:
    match at:
        case AssociationType.THIS_JOINS:
            return 1
        case AssociationType.OTHER_JOINS:
            return 2
        case AssociationType.THIS_DIVIDES:
            return 3
        case AssociationType.OTHER_DIVIDES:
            return 4


def string_to_association_type(string: str) -> Optional[AssociationType]:
    if string == "JOINS_TO":
        return AssociationType.THIS_JOINS
    if string == "JOINS_WITH":
        return AssociationType.OTHER_JOINS
    if string == "DIVIDES_TO":
        return AssociationType.THIS_DIVIDES
    if string == "DIVIDES_FROM":
        return AssociationType.OTHER_DIVIDES
    return None

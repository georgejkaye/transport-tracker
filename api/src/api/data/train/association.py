from enum import Enum
from typing import Optional


AssociatedType = Enum(
    "AssociatedType",
    ["THIS_JOINS", "OTHER_JOINS", "THIS_DIVIDES", "OTHER_DIVIDES"],
)


def string_of_associated_type(at: AssociatedType) -> str:
    match at:
        case AssociatedType.THIS_JOINS:
            return "THIS_JOINS"
        case AssociatedType.OTHER_JOINS:
            return "OTHER_JOINS"
        case AssociatedType.THIS_DIVIDES:
            return "THIS_DIVIDES"
        case AssociatedType.OTHER_DIVIDES:
            return "OTHER_DIVIDES"


def string_to_associated_type(string: str) -> Optional[AssociatedType]:
    if string == "JOINS_TO":
        return AssociatedType.THIS_JOINS
    if string == "JOINS_WITH":
        return AssociatedType.OTHER_JOINS
    if string == "DIVIDES_TO":
        return AssociatedType.THIS_DIVIDES
    if string == "DIVIDES_FROM":
        return AssociatedType.OTHER_DIVIDES
    return None

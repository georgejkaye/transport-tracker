from dataclasses import dataclass
from typing import Optional
from psycopg import Connection

from api.utils.database import register_type


@dataclass
class BusOperatorDetails:
    id: int
    name: str
    national_code: str
    bg_colour: Optional[str]
    fg_colour: Optional[str]


def register_bus_operator_details(
    id: int,
    name: str,
    national_code: str,
    bg_colour: Optional[str],
    fg_colour: Optional[str],
) -> BusOperatorDetails:
    return BusOperatorDetails(
        id, name, national_code, bg_colour or "#ffffff", fg_colour or "#000000"
    )


def register_bus_operator_details_types(conn: Connection) -> None:
    register_type(conn, "BusOperatorDetails", register_bus_operator_details)

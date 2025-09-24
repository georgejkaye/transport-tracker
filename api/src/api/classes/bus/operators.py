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


def register_bus_operator_details(conn: Connection) -> None:
    register_type(conn, "BusOperatorDetails", BusOperatorDetails)

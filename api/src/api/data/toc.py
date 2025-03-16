from typing import Optional

from dataclasses import dataclass
from psycopg import Connection


def select_operator_id(conn: Connection, operator_name: str) -> Optional[str]:
    statement = """
        SELECT operator_id
        FROM Operator
        WHERE operator_name = %(name)s
    """
    rows = conn.execute(statement, {"name": operator_name}).fetchall()
    if len(rows) != 1:
        return None
    row = rows[0]
    return row[0]


@dataclass
class OperatorData:
    id: int
    code: str
    name: str
    bg: Optional[str]
    fg: Optional[str]


@dataclass
class BrandData:
    id: int
    code: str
    name: str
    bg: Optional[str]
    fg: Optional[str]

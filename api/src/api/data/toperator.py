from dataclasses import dataclass
from typing import Optional
from psycopg2._psycopg import cursor


def select_operator_id(cur: cursor, operator_name: str) -> Optional[str]:
    statement = """
        SELECT operator_id
        FROM Operator
        WHERE operator_name = %(name)s
    """
    cur.execute(statement, {"name": operator_name})
    rows = cur.fetchall()
    if len(rows) != 1:
        return None
    row = rows[0]
    return row[0]


@dataclass
class OperatorData:
    code: str
    name: str


@dataclass
class BrandData:
    code: str
    name: str

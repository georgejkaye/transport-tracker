from dataclasses import dataclass
from typing import Optional
from psycopg import Connection

from api.utils.database import register_type


@dataclass
class OperatorData:
    id: int
    code: str
    name: str
    bg: Optional[str]
    fg: Optional[str]


def register_operator_data(
    operator_id: int,
    operator_code: str,
    operator_name: str,
    operator_bg: str,
    operator_fg: str,
) -> OperatorData:
    return OperatorData(
        operator_id, operator_code, operator_name, operator_bg, operator_fg
    )


@dataclass
class BrandData:
    id: int
    code: str
    name: str
    bg: Optional[str]
    fg: Optional[str]


def register_brand_data(
    brand_id: int,
    brand_code: str,
    brand_name: str,
    brand_bg: str,
    brand_fg: str,
) -> BrandData:
    return BrandData(brand_id, brand_code, brand_name, brand_bg, brand_fg)


def register_brand_data_types(conn: Connection) -> None:
    register_type(conn, "OutBrandData", register_brand_data)

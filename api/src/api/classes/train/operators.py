from dataclasses import dataclass
from datetime import date
from typing import Optional
from psycopg import Connection
from psycopg.types.range import Range

from api.utils.database import register_type


@dataclass
class BrandData:
    brand_id: int
    brand_code: str
    brand_name: str
    brand_bg: Optional[str]
    brand_fg: Optional[str]


@dataclass
class OperatorData:
    operator_id: int
    operator_code: str
    operator_name: str
    operator_bg: Optional[str]
    operator_fg: Optional[str]
    operation_range: Range[date]
    operator_brands: list[BrandData]


def register_train_operator_out_data(conn: Connection) -> None:
    register_type(conn, "train_brand_out_data", BrandData)

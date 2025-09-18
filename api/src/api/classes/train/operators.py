from dataclasses import dataclass
from datetime import date
from typing import Optional

from psycopg.types.range import Range


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
    operation_range_start: Optional[date]
    operation_range_end: Optional[date]
    operator_brands: list[BrandData]


@dataclass
class OperatorDbData:
    operator_id: int
    operator_code: str
    operator_name: str
    operator_bg: Optional[str]
    operator_fg: Optional[str]
    operation_range: Range[date]
    operator_brands: list[BrandData]


def operator_db_data_to_operator_data(db_data: OperatorDbData) -> OperatorData:
    return OperatorData(
        db_data.operator_id,
        db_data.operator_code,
        db_data.operator_name,
        db_data.operator_bg,
        db_data.operator_fg,
        db_data.operation_range.lower,
        db_data.operation_range.upper,
        db_data.operator_brands,
    )


@dataclass
class DbOperatorDetails:
    operator_id: int
    is_brand: bool
    operator_code: str
    operator_name: str
    bg_colour: str
    fg_colour: str


@dataclass
class OperatorBrandLookup:
    operators: dict[int, DbOperatorDetails]
    brands: dict[int, DbOperatorDetails]

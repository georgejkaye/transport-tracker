from dataclasses import dataclass
from datetime import date
from typing import Optional

from psycopg import Connection
from psycopg.types.range import Range

from api.db.types.train.operator import TrainOperatorDetailsOutData
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
    operation_range_start: Optional[date]
    operation_range_end: Optional[date]
    operator_brands: list[BrandData]


@dataclass
class DbTrainOperatorOutData:
    operator_id: int
    operator_code: str
    operator_name: str
    operator_bg: Optional[str]
    operator_fg: Optional[str]
    operation_range: Range[date]
    operator_brands: list[BrandData]


def register_train_operator_out_data(conn: Connection):
    register_type(conn, "train_operator_out_data", DbTrainOperatorOutData)


def operator_db_data_to_operator_data(
    db_data: DbTrainOperatorOutData,
) -> OperatorData:
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
class DbTrainOperatorDetailsOutData:
    operator_id: int
    is_brand: bool
    operator_code: str
    operator_name: str
    bg_colour: str
    fg_colour: str


def register_train_operator_details_out_data(conn: Connection) -> None:
    register_type(
        conn, "train_operator_details_out_data", DbTrainOperatorDetailsOutData
    )


@dataclass
class OperatorBrandLookup:
    operators: dict[int, TrainOperatorDetailsOutData]
    brands: dict[int, TrainOperatorDetailsOutData]

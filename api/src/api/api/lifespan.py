from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from networkx import MultiDiGraph
from psycopg import Connection

from api.classes.train.operators import OperatorBrandLookup
from api.db.functions.select.train.operator import (
    select_operator_details_fetchall,
)
from api.db.types.register import register_types
from api.db.types.train.operator import TrainOperatorDetailsOutData
from api.library.networkx import load_osmnx_graphml
from api.utils.environment import get_env_variable, get_secret

network_path = get_env_variable("NETWORK_PATH")

conn: Optional[Connection] = None
network: Optional[MultiDiGraph[int]] = None
operator_brand_lookup: Optional[OperatorBrandLookup] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    if (network_path) is None:
        raise RuntimeError("Could not get environment variable NETWORK_PATH")
    global conn
    conn = Connection.connect(
        dbname=get_env_variable("DB_NAME"),
        user=get_env_variable("DB_USER"),
        password=get_secret("DB_PASSWORD"),
        host=get_env_variable("DB_HOST"),
    )
    register_types(conn)
    print("Initialised db connection")
    global network
    network = load_osmnx_graphml(network_path)  # type: ignore
    print("Initialised train network")
    global operator_brand_lookup
    operator_brand_lookup = initialise_train_operator_brand_lookup(conn)
    print("Initialised train operator brand lookup")
    yield
    print("Shutting down db connectionn")
    conn.close()


def get_db_connection() -> Connection:
    if conn is None:
        raise RuntimeError("DB connection not initialised")
    return conn


def get_network() -> MultiDiGraph[int]:
    if network is None:
        raise RuntimeError("Network not initialised")
    return network


def get_operator_brand_lookup() -> OperatorBrandLookup:
    if operator_brand_lookup is None:
        raise RuntimeError("Operator brand lookup not initialised")
    return operator_brand_lookup


def get_train_operator_brand_colour(
    operator_id: int, brand_id: Optional[int]
) -> Optional[str]:
    operator_brand_lookup = get_operator_brand_lookup()
    if (
        brand_id is not None
        and (brand := operator_brand_lookup.brands.get(brand_id)) is not None
    ):
        return brand.bg_colour
    if (
        operator := operator_brand_lookup.operators.get(operator_id)
    ) is not None:
        return operator.bg_colour
    return "#000000"


def initialise_train_operator_brand_lookup(
    conn: Connection,
) -> OperatorBrandLookup:
    operator_details = select_operator_details_fetchall(conn)
    operators: dict[int, TrainOperatorDetailsOutData] = {}
    brands: dict[int, TrainOperatorDetailsOutData] = {}
    for operator in operator_details:
        if operator.is_brand:
            brands[operator.operator_id] = operator
        else:
            operators[operator.operator_id] = operator
    return OperatorBrandLookup(operators, brands)

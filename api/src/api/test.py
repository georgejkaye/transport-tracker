import os
from pathlib import Path

from psycopg import Connection

from api.api.lifespan import (
    get_train_operator_brand_colour_by_lookup,
    initialise_train_operator_brand_lookup,
)
from api.db.types.register import register_types
from api.library.networkx import load_osmnx_graphml
from api.network.map import get_leg_map_page_by_leg_id

conn = Connection.connect(
    host="localhost", dbname="transport", user="transport", password="transport"
)
register_types(conn)

network = load_osmnx_graphml(
    Path(os.path.realpath(__file__)).parent.parent.parent
    / "data"
    / "network.gml"
)

operator_brand_lookup = initialise_train_operator_brand_lookup(conn)

html = get_leg_map_page_by_leg_id(
    conn,
    network,
    1151,
    lambda opid, brid: get_train_operator_brand_colour_by_lookup(
        operator_brand_lookup, opid, brid
    ),
)

print(html)
